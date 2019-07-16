from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import os
import folium
import statistics
import json

class ImageMetaData(object):
    '''
    Extract the exif data from any image. Data includes GPS coordinates, 
    Focal Length, Manufacture, and more.
    '''
    exif_data = None
    image = None

    def __init__(self, img_path):
        self.image = Image.open(img_path)
        #print(self.image._getexif())
        self.get_exif_data()
        super(ImageMetaData, self).__init__()

    def get_exif_data(self):
        """Returns a dictionary from the exif data of an PIL Image item. Also converts the GPS Tags"""
        exif_data = {}
        info = self.image._getexif()
        if info:
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "GPSInfo":
                    gps_data = {}
                    for t in value:
                        sub_decoded = GPSTAGS.get(t, t)
                        gps_data[sub_decoded] = value[t]

                    exif_data[decoded] = gps_data
                else:
                    exif_data[decoded] = value
        self.exif_data = exif_data
        return exif_data

    def get_if_exist(self, data, key):
        if key in data:
            return data[key]
        return None

    def convert_to_degress(self, value):

        """Helper function to convert the GPS coordinates 
        stored in the EXIF to degress in float format"""
        d0 = value[0][0]
        d1 = value[0][1]
        d = float(d0) / float(d1)

        m0 = value[1][0]
        m1 = value[1][1]
        m = float(m0) / float(m1)

        s0 = value[2][0]
        s1 = value[2][1]
        s = float(s0) / float(s1)

        return d + (m / 60.0) + (s / 3600.0)

    def get_lat_lng(self):
        """Returns the latitude and longitude, if available, from the provided exif_data (obtained through get_exif_data above)"""
        lat = None
        lng = None
        exif_data = self.get_exif_data()
        #print(exif_data)
        if "GPSInfo" in exif_data:      
            gps_info = exif_data["GPSInfo"]
            gps_latitude = self.get_if_exist(gps_info, "GPSLatitude")
            gps_latitude_ref = self.get_if_exist(gps_info, 'GPSLatitudeRef')
            gps_longitude = self.get_if_exist(gps_info, 'GPSLongitude')
            gps_longitude_ref = self.get_if_exist(gps_info, 'GPSLongitudeRef')
            if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
                lat = self.convert_to_degress(gps_latitude)
                if gps_latitude_ref != "N":                     
                    lat = 0 - lat
                lng = self.convert_to_degress(gps_longitude)
                if gps_longitude_ref != "E":
                    lng = 0 - lng

        return lat, lng

def main():
    imagesBasePath='static/images/'

    folders = []

    # r=root, d=directories, f = files
    for r, d, f in os.walk(imagesBasePath):
        for folder in d:
            folders.append(os.path.join(r, folder))
        break

    for folder in folders:

        longs = []
        lats = []

        # print(folder)
        files = []
        # r=root, d=directories, f = files
        for r, d, f in os.walk(folder):
            for file in f:
                if '.DS_Store' not in file and '.html' not in file:
                    files.append(os.path.join(r, file))

        for f in files:
            print(f)
            coord = ImageMetaData(f).get_lat_lng()

            if coord[0] != 'None' and coord[1] != 'None':
                try:
                    lats.append(float(coord[0]))
                    longs.append(float(coord[1]))
                except:
                    pass

        try:
            print('toto')
            with open('static/maps/' + folder.split('/')[2] + '.json') as json_file:  
                data = json.load(json_file)
                m = folium.Map(location=[data["base_lat"], data["base_long"]], zoom_start=data["zoom"])
        except:
            m = folium.Map(location=[sum(lats)/len(lats), sum(longs)/len(longs)])

        # m = folium.Map(location=[statistics.mean(lats), statistics.mean(longs)], min_lat=min(lats), max_lat=max(lats), min_lon=min(longs), max_lon=max(longs))

        for i in range(len(lats)):
            folium.Marker(
                location=[lats[i], longs[i]],
                icon=folium.Icon(color='green')
            ).add_to(m)

        m.save('static/maps/' + folder.split('/')[2] + '.html')

main()