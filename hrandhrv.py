import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math
measures = {} #empty dictionary to add to

def get_data(filename):
   dataset = pd.read_csv(filename)
   return dataset

def rolmean(dataset, hrw, fs):
   mov_avg = dataset['hart'].rolling(int(hrw*fs)).mean() # calculate moving average
   avg_hr = (np.mean(dataset.hart))
   mov_avg = [avg_hr if math.isnan(x) else x for x in mov_avg]
   mov_avg = [x*1.2 for x in mov_avg] # and *20%
   dataset['hart_rollingmean'] = mov_avg #append the moving average to the dataframe

def detect_peaks(dataset):
   #mark regions of interest
   window = []
   peaklist = []
   listpos = 0 #use a counter to move over the different data columns
   for datapoint in dataset.hart:
       rollingmean = dataset.hart_rollingmean[listpos]  #get local mean
       if (datapoint < rollingmean) and (len(window) < 1): #if theres no detectable -> do nothing
           listpos += 1
       elif (datapoint > rollingmean): #if the signal comes above local mean -> mark ROI
           window.append(datapoint)
           listpos += 1
       else: #if the signal drops below local mean -> determine highest point
           maximum = max(window)
           beatposition = listpos - len(window) + (window.index(max(window))) #note the position of the high point on the X-axis
           peaklist.append(beatposition) #add the detected peak high point to list
           window = [] #clear the marked ROI
           listpos += 1
   measures['peaklist'] = peaklist
   measures['ybeat'] = [dataset.hart[x] for x in peaklist]

def calc_RR(dataset, fs):
   RR_list = [] #R-R interval of signal
   peaklist = measures['peaklist']
   count = 0
   while (count < (len(peaklist)-1)):
       RR_interval = (peaklist[count+1] - peaklist[count]) #calculate distance between beats in no of samples
       ms_dist = ((RR_interval / fs) * 1000.0) #convert sample distances to ms distances
       RR_list.append(ms_dist) #append to list
       count += 1
   measures['RR_list'] = RR_list

def calc_bpm():
   RR_list = measures['RR_list']
   measures['bpm'] = 60000 / np.mean(RR_list) #60000 ms (1 minute) / average R-R interval of signal

def plotter(dataset, title):
   peaklist = measures['peaklist']
   ybeat = measures['ybeat']
   plt.title(title)
   plt.plot(dataset.hart, alpha=0.5, color='blue', label="raw signal")
   plt.plot(dataset.hart_rollingmean, color ='green', label="moving average")
   plt.scatter(peaklist, ybeat, color='red', label="average: %.1f BPM" %measures['bpm'])
   plt.legend(loc=4, framealpha=0.6)
   plt.show()

def process(dataset, hrw, fs): #hrw is the one-sided window size (used 0.75) and fs is the sample rate (data is recorded at 100Hz)
   rolmean(dataset, hrw, fs)
   detect_peaks(dataset)
   calc_RR(dataset, fs)
   calc_bpm()
   plotter(dataset, "My Heartbeat Plot")

dataset = pd.read_csv("data.csv")
process(dataset, 0.75, 100)

#We have imported our Python module as an object called 'hb'
#This object contains the dictionary 'measures' with all values in it
#Now we can also retrieve the BPM value (and later other values) like this:
bpm = measures['bpm']
#to view all objects in the dictionary, use "keys()" like so:
#print hb.measures.keys()

'''
HRV ITEMS
IBI (inter-beat interval): the mean distance of intervals between heartbeats
SDNN: the standard deviation of intervals between heartbeats
SDSD: the standard deviation of successive differences between adjacent R-R intervals
RMSSD: the root mean square of successive differences between adjacent R-R intervals
pNN50/pNN20: the proportion of differences greater than 50ms / 20ms
The frequency spectrum is calculated performing a Fast Fourier Transform over the R-R interval dataseries.
Method: fast compared to the Discrete Fourier Transform method. The larger the dataset, the larger the speed difference between the methods.
Re-sample the signal ton estimate the spectrum
then transform the re-sampled signal to the frequency domain
then integrate the area under the curve at given intervals
NEED lists of
positions of all R-peaks - detect_peaks() function in dict[‘peaklist’]
intervals between all subsequent R-R pairs (RR1, RR2,.. RR-n) - calc_RR() function in dict[‘RR_list’]
differences between all subsequent intervals between R-R pairs (RRdiff1,… RRdiffn)
squared differences between all subsequent differences between R-R pairs
- use dict[‘RR_list’] and calculate both the differences and the squared differences between adjacent values
'''

RR_diff = []
RR_sqdiff = []
RR_list = measures['RR_list']
count_diff = 1 #use a counter to iterate over the RR_list
while (count_diff < (len(RR_list)-1)): #leep going as long as there are R-R intervals
   RR_diff.append(abs(RR_list[count_diff] - RR_list[count_diff+1])) #xalculates absolute difference between successive R-R interval
   RR_sqdiff.append(math.pow(RR_list[count_diff] - RR_list[count_diff+1], 2)) #calculates squared difference
   count_diff += 1
print (RR_diff, RR_sqdiff)
ibi = np.mean(RR_list) #the mean of RR_list is the mean Inter Beat Interval
print ("IBI:", ibi)
sdnn = np.std(RR_list) #stdev of all R-R intervals
print ("SDNN:", sdnn)
sdsd = np.std(RR_diff) #take stdev of the differences between all subsequent R-R intervals
print ("SDSD:", sdsd)
rmssd = np.sqrt(np.mean(RR_sqdiff)) #Take root of the mean of the list of squared differences
print ("RMSSD:", rmssd)
nn20 = [x for x in RR_diff if (x>20)] #first create a list of all values over 20, 50
nn50 = [x for x in RR_diff if (x>50)]
pnn20 = float(len(nn20)) / float(len(RR_diff)) #calculate the proportion of NN20, NN50 intervals to all intervals
pnn50 = float(len(nn50)) / float(len(RR_diff)) #float so no rounding
print ("pNN20, pNN50:", pnn20, pnn50)

'''new functions'''

def calc_RR(dataset, fs):
   peaklist = measures['peaklist']
   RR_list = []
   cnt = 0
   while (cnt < (len(peaklist)-1)):
       RR_interval = (peaklist[cnt+1] - peaklist[cnt])
       ms_dist = ((RR_interval / fs) * 1000.0)
       RR_list.append(ms_dist)
       cnt += 1
   RR_diff = []
   RR_sqdiff = []
   cnt = 0
   while (cnt < (len(RR_list)-1)):
       RR_diff.append(abs(RR_list[cnt] - RR_list[cnt+1]))
       RR_sqdiff.append(math.pow(RR_list[cnt] - RR_list[cnt+1], 2))
       cnt += 1
   measures['RR_list'] = RR_list
   measures['RR_diff'] = RR_diff
   measures['RR_sqdiff'] = RR_sqdiff

def calc_ts_measures():
   RR_list = measures['RR_list']
   RR_diff = measures['RR_diff']
   RR_sqdiff = measures['RR_sqdiff']
   measures['bpm'] = 60000 / np.mean(RR_list)
   measures['ibi'] = np.mean(RR_list)
   measures['sdnn'] = np.std(RR_list)
   measures['sdsd'] = np.std(RR_diff)
   measures['rmssd'] = np.sqrt(np.mean(RR_sqdiff))
   NN20 = [x for x in RR_diff if (x>20)]
   NN50 = [x for x in RR_diff if (x>50)]
   measures['nn20'] = nn20
   measures['nn50'] = nn50
   measures['pnn20'] = float(len(NN20)) / float(len(RR_diff))
   measures['pnn50'] = float(len(NN50)) / float(len(RR_diff))
#update the process function to include new functions

def process(dataset, hrw, fs):
   rolmean(dataset, hrw, fs)
   detect_peaks(dataset)
   calc_RR(dataset, fs)
   calc_ts_measures()