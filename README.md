# telegra.ph-album-creator

Simple script for creating album as a telegra.ph page based on [python273/telegraph](https://github.com/python273/telegraph/releases/tag/v1.4.1)

## Options:

|  |  |  |
| --- | --- | --- |
| -i, --input | Input folder | Path to folder witch contains albums to upload. _required_ |
| -o, --output | Output folder | Folder to keep uploaded albums. _optional_ |
| -t, --token | Account token | Account token to keep the ability to edit page in the future<br/>(if empty — will be generated).<br/>Can also be specified inside the script. _optional_ |
| -p, --pause | Upload pause in seconds | Pause between image upload operations. _optional_ | 
| -wi, --width | Maximum image width | Images that exceed the maximum width will be downscaled. (default value 5000). _optional_ | 
| -he, --height | Maximum image height | Images that exceed the maximum height will be reduced. (default value 5000). _optional_ | 
| -s, --size | Maximum image file size | Images larger than the maximum size will be compressed. Specified in bytes. (default value 5000000). _optional_ | 


### Note
>The maximum image sizes and dimensions in telegra.ph are not disclosed, but some empirical research has revealed a simple rule: the width and height must be less than or equal to 10,000 pixels in total, and the file size must not exceed 5 MB. These restrictions are set in the script by default and can be changed using command line arguments.


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


