import numpy as np

sensor_data = np.array([
    [1, 22.5, 45.2, 1012.8],
    [2, 22.7, 45.0, 1012.6],
    [3, 22.6, 44.9, 1012.7],
    [4, 22.8, 45.3, 1012.5],
    [5, 23.0, 45.1, 1012.4],
    [6, 23.2, 44.8, 1012.3],
    [7, 22.9, 45.0, 1012.4],
    [8, 23.1, 44.7, 1012.2],
    [9, 22.8, 45.1, 1012.5],
    [10, 30.5, 60.0, 1005.0]
])

# to select only feature , time is not feature
features = sensor_data[:, 1:]

window = 3

# using only temparature 
temperature = features[:, 0]

rolling_mean = np.array([
    np.mean(temperature[i:i+window])
    for i in range(len(temperature)-window+1)
])

rolling_std = np.array([
    np.std(temperature[i:i+window])
    for i in range(len(temperature)-window+1)
])

mean = np.mean(features, axis=0)
std = np.std(features, axis=0)

z_scores = (features - mean) / std

outlier_rows = np.any(np.abs(z_scores) > 2, axis=1)

print("Rolling Mean:", rolling_mean)

print("Rolling Std:", rolling_std)

print("Z-scores:", z_scores)

print("Outlier Rows:", outlier_rows)

print("Outlier Data:", sensor_data[outlier_rows])