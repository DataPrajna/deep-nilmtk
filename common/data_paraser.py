from nilmtk import DataSet
import matplotlib.pyplot as plt
plt.ion()
from networkx.drawing.nx_agraph import graphviz_layout
import networkx as nx
from nilmtk.disaggregate import CombinatorialOptimisation
from nilmtk import HDFDataStore, MeterGroup

class VisualizeApplianceData:

    def __init__(self, filename):
        self.data = DataSet(filename).buildings

    def get_elec_meter_data_of_a_building(self, building_idx):
        return  self.data[building_idx].elec

    def get_appliance_data_of_a_building(self, building_idx, appliance_name):
        return self.get_elec_meter_data_of_a_building(building_idx)[appliance_name]

    def plot_appliance_data_of_a_building(self, building_idx, appliance_name):
         activations = self.get_appliance_data_of_a_building(building_idx, appliance_name).power_series()
         activations = iter(activations)
         for interval_activation in  activations:
             plt.plot(interval_activation)
             plt.show()
             plt.waitforbuttonpress()
             plt.gcf().clear()



    def plot_main_meter_data_of_a_building(self, building_idx):
        activations = self.get_elec_meter_data_of_a_building(building_idx).mains().power_series()
        activations = iter(activations)
        for interval_activation in activations:
            plt.plot(interval_activation)
            plt.show()
            plt.waitforbuttonpress()
            plt.gcf().clear()

    def get_all_appliances_of_a_building(self, building_idx):
        all_applicances = self.get_elec_meter_data_of_a_building(building_idx).appliances
        return [a.identifier.type for a in all_applicances]

    def wiring_graph(self, meters):
        """Returns a networkx.DiGraph of connections between meters."""
        wiring_graph = nx.DiGraph()

        def _build_wiring_graph(meters):
            for meter in meters:
                if isinstance(meter, MeterGroup):
                    metergroup = meter
                    _build_wiring_graph(metergroup.meters)
                else:
                    upstream_meter = meter.upstream_meter(raise_warning=False)
                    # Need to ensure we use the same object
                    # if upstream meter already exists.
                    if upstream_meter is not None:
                        for node in wiring_graph.nodes():
                            if upstream_meter == node:
                                upstream_meter = node
                                break
                        wiring_graph.add_edge(upstream_meter, meter)

        _build_wiring_graph(meters)
        return wiring_graph

    def draw_wire_between_mains_and_submeter_of_abuilding(self, building_idx, show_label=True):
        meters = self.get_elec_meter_data_of_a_building(building_idx).meters
        graph = self.wiring_graph(meters)
        meter_labels = {meter: meter.instance() for meter in graph.nodes()}
        pos = graphviz_layout(graph, prog='dot')
        nx.draw(graph, pos, labels=meter_labels, arrows=False)

        if show_label:
            meter_labels = {meter: meter.label() for meter in graph.nodes()}
            for meter, name in meter_labels.iteritems():
                x, y = pos[meter]
                if meter.is_site_meter():
                    delta_y = 5
                else:
                    delta_y = -5
                plt.text(x, y + delta_y, s=name, bbox=dict(facecolor='green', alpha=0.5),
                         horizontalalignment='center')
        ax = plt.gca()
        return graph, ax

    def pie_plot_of_submeter_energy_of_a_building(self, building_index):
        elec = self.get_elec_meter_data_of_a_building(building_index)
        fraction = elec.submeters().fraction_per_meter().dropna()
        labels = elec.get_labels(fraction.index)
        plt.figure(figsize=(10, 10))
        fraction.plot(kind='pie', labels=labels);
        plt.show()

    def fit_a_model(self, building_idx):
        co = CombinatorialOptimisation()
        elec = self.get_elec_meter_data_of_a_building(building_idx)
        co.train(elec)
        return co

    def disaggregate_building_to_file(self, building_idx, filename, model=None):
        if model == None:
            model = self.fit_a_model(building_idx)
        elec = self.get_elec_meter_data_of_a_building(building_idx)

        output = HDFDataStore(filename, 'w')
        model.disaggregate(elec.mains(), output)
        output.close()



















