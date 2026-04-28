# Til GUI
class DataGrapher:
    """Class to graph the data collected from the AMRs and Raspberry Pi."""
    def __init__(self):
        self.data = []

    def add_data(self, data_point):
        self.data.append(data_point)

    def display_data(self):
        for data_point in self.data:
            print(data_point)