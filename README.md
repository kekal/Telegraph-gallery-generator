# telegra.ph-album-creator

Simple script for creating album as a telegra.ph page.

## Options:

|  |  |  |
| --- | --- | --- |
| -i, --input | Input folder | Path to folder witch contains albums to upload. _required_ |
| -o, --output | Output folder | Folder to keep uploaded albums. _optional_ |
| -t, --token | Account token | Account token to keep the ability to edit page in the future<br/>(if empty — will be generated).<br/>Can also be specified inside the script. _optional_ |
| -p, --pause | Upload pause in seconds | Pause between image upload operations. _optional_ | 


## Example

Have a folder TELEGRAPH with two albums inside:
```
TELEGRAPH
├───Album_Train_2022-05-17
│       Image1.jpg
│       Image2.jpg
│       Image3.jpg
│       Image4.jpg
│
└───Album_Sunset_2022-05-23
        photo1.jpg
        photo1.jpg
```
Run the command:
`python upload.telegraph.py -i H:\TELEGRAPH`

Result:
```
TELEGRAPH
│   log.txt
│   results.txt
│
└───old
    ├───Album_Train_2022-05-17
    │       Image1.jpg
    │       Image2.jpg
    │       Image3.jpg
    │       Image4.jpg
    │
    └───Album_Sunset_2022-05-23
            photo1.jpg
            photo2.jpg
```

Each time results.txt will be appended with a record of newly created albums:

Album_Sunset_2022-05-23 : 2 : https://telegra.ph/Album-Sunset-2022-05-23-10-05-2

Album_Train_2022-05-17 : 4 : https://telegra.ph/Album-Train-2022-05-17-10-05-2


