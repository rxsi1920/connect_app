import pandas as pd
from sklearn.cluster import DBSCAN

# Load the original CSV file
df = pd.read_csv('fake_user_data_scarce.csv')

# Perform DBSCAN clustering
dbscan = DBSCAN(eps=0.045, min_samples=1, metric='euclidean')
df['Cluster'] = dbscan.fit_predict(df[['Latitude', 'Longitude']])

# Define interest columns
interest_columns = df.columns[4:34].tolist()

# Convert interests to binary string
df['Interests'] = df[interest_columns].apply(lambda row: ''.join(row.astype(int).astype(str)), axis=1)

# Function to convert hourly availability to binary string
def hours_to_binary(row, day):
    return ''.join(row[[f'{day}_hour_{i}' for i in range(24)]].astype(int).astype(str))

# Convert availability for each day to binary
for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
    df[day] = df.apply(lambda row: hours_to_binary(row, day), axis=1)

# Select columns for the optimized DataFrame
columns_to_keep = ['UserID', 'Name', 'Latitude', 'Longitude', 'Cluster', 'Interests', 
                   'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# Create the optimized DataFrame
df_optimized = df[columns_to_keep]

# Initialize a list to store the subgroups
subgroups = []

# Track the total number of clusters
total_clusters = len(df_optimized['Cluster'].unique())
cluster_iteration = 0

# Function to build subgroups
def generate_subgroups(cluster_df, cluster_id):
    global cluster_iteration
    cluster_iteration += 1
    print(f"Processing Cluster {cluster_iteration} of {total_clusters} (Cluster ID: {cluster_id})")

    # Step 1: Iterate over each interest within the cluster
    for interest_index, interest in enumerate(interest_columns, start=1):
        interested_users = cluster_df[cluster_df['Interests'].apply(lambda x: x[interest_index-1] == '1')]

        if len(interested_users) >= 2:
            # Step 2: Group by weekday
            for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                available_users = interested_users[interested_users[day].apply(lambda x: '1' in x)]

                if len(available_users) >= 2:
                    # Step 3: Group by timeslot (hour of the day)
                    for hour in range(24):
                        hour_available_users = available_users[available_users[day].apply(lambda x: x[hour] == '1')]

                        if len(hour_available_users) >= 2:
                            subgroup = {
                                'GeoCluster': cluster_id,
                                'Interest': interest_index,
                                'Day': day,
                                'Hour': hour,
                                'Users': ','.join(map(str, hour_available_users['UserID'].tolist())),
                                'Size': len(hour_available_users)
                            }
                            subgroups.append(subgroup)
                            print(f"  Subgroup found: Cluster {cluster_id}, Interest {interest_index}/{len(interest_columns)}, Day {day}, Hour {hour}, Size {len(hour_available_users)}")

# Apply subgroup creation to each geographic cluster
for cluster_id, cluster_df in df_optimized.groupby('Cluster'):
    generate_subgroups(cluster_df, cluster_id)
