from nilmtk import dataset
from os.path import join
import pandas as pd
import numpy as np
import h5py
class DataServer:
    def __init__(self, filename):
        self.data = dataset.DataSet(filename)

    def set_metadata(self, building_number, num_class):
        elec = self.data.buildings[building_number].elec
        self.top_train_elec = elec.submeters().select_top_k(k=num_class)

    def prepare_data(self):
        appliance_name_to_id = {
            'dish washer':0,
            'fridge':1,
            'light':2,
            'washer dryer':3,
            'microwave':4,
            'sockets':5,
            'electric furnace':6,
            'electric stove':7}

        self.samples = []
        self.labels = []


        for building in range(1, 4):
            self.set_metadata(building, 5)
            all_sub_meters =  self.top_train_elec.submeters().meters

            x = pd.core.series.Series(range(0, 400), index=range(0, 400))

            for m in all_sub_meters:
                good_sections = m.get_activations(sample_period=10)
                for gs in good_sections:
                    gs.index = range(0, len(gs))
                    aligned = gs.align(x)
                    aligned = aligned[0].interpolate(method='linear')[0:400]
                    self.labels.append([appliance_name_to_id[m.appliances[0].type['type']]])
                    self.samples.append(aligned.values)


        self.samples = np.asarray(self.samples)
        self.labels = np.asarray(self.labels)

    def save(self, filename):
        file = h5py.File(filename, 'w')
        file.create_dataset(name='samples', data=self.samples)
        file.create_dataset(name='labels', data=self.labels)
        file.close()


if __name__== "__main__":
    data_dir = "/Data/"
    building_number = 3
    ds = DataServer(join(data_dir, 'redd.h5'))
    ds.set_metadata(building_number, 5)
    ds.prepare_data()
    ds.save('b1to5top5.h5')
    p = [len(x) for x in ds.samples]
    print(np.mean(p))
    print(len(ds.labels))
    print(ds.samples.shape)
    print(ds.labels.shape)







