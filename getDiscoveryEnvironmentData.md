# Discovery Environment Data

Some datasets are not stored in GEOME and we need to process them separately.  

## 1. get started with iCommands
need iCommands installed on your system to grab data
https://cyverse-data-store-guide.readthedocs-hosted.com/en/latest/step2.html#icommands-installation-for-linux


## 2. iCommands syntax and fetching protocol
Data will go into the de_data directory.  We want to commit just this directory
into github but don't need to store any actual data.

Directory listing:
```
ils /iplant/home/rwalls/FuTRES_data/ValidatedData
```
Fetch data:
The following just fetches file by file.
```
cd de_data
iget -PT /iplant/home/rwalls/FuTRES_data/ValidatedData/FuTRES_Mammals_VertNet_Global_Modern_1.csv .
iget -PT /iplant/home/rwalls/FuTRES_data/ValidatedData/FuTRES_Mammals_VertNet_Global_Modern_2.csv .
iget -PT /iplant/home/rwalls/FuTRES_data/ValidatedData/FuTRES_Mammals_VertNet_Global_Modern_3.csv .
iget -PT /iplant/home/rwalls/FuTRES_data/ValidatedData/FuTRES_Mammals_VertNet_Global_Modern_4.csv .
iget -PT /iplant/home/rwalls/FuTRES_data/ValidatedData/FuTRES_Mammals_VertNet_Global_Modern_5.csv .
iget -PT /iplant/home/rwalls/FuTRES_data/ValidatedData/FuTRES_Mammals_VertNet_Global_Modern_6.csv .
iget -PT /iplant/home/rwalls/FuTRES_data/ValidatedData/FuTRES_Mammals_VertNet_Global_Modern_7.csv .
iget -PT /iplant/home/rwalls/FuTRES_data/ValidatedData/FuTRES_Mammals_VertNet_Global_Modern_8.csv .
iget -PT /iplant/home/rwalls/FuTRES_data/ValidatedData/FuTRES_Mammals_VertNet_Global_Modern_9.csv .
iget -PT /iplant/home/rwalls/FuTRES_data/ValidatedData/FuTRES_Mammals_VertNet_Global_Modern_10.csv .

```


## 3. Process data
Processing syntax is a function called in the fetch.py script