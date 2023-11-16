import json
class KPIResultSetTrue:

    true_kpis_dict = None


    def __init__(self,test_path,test_name) -> None:
        self.true_kpis_dict = json.load(open(test_path+test_name[0:-4]+".json"))

    def evaluate() -> float:
        pass