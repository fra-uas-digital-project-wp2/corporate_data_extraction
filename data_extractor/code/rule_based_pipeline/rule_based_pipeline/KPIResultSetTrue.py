import json
class KPIResultSetTrue:

    true_kpis_dict = None
    result = [[],[],[]]

    def __init__(self,test_path,test_name) -> None:
        self.true_kpis_dict = json.load(open(test_path+test_name[0:-4]+".json"))

    def evaluate(self,kpiresults) -> float:

        for scope,true in self.true_kpis_dict.items():
            for (y, v, p) in zip(true.get("Year"),true.get("Value"), true.get("Page")):
                for value in kpiresults:
                    if (true.get("ID") != value.kpi_id) or (y != value.year):
                        continue
                    print(true.get("ID"), " : " ,  value.kpi_id, " :: " ,y, " : ", value.year)
                    if (str(v) == value.value) and (p == value.page_num):
                        self.result[true.get("ID")-6].append(True)
                    else:
                        self.result[true.get("ID")-6].append(False)

    def printEval(self):
        print(self.result)

            


     