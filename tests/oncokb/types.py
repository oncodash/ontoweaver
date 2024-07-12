import sys
import ontoweaver

class sample(ontoweaver.Node):
    @staticmethod
    def fields():
        return []

class patient(ontoweaver.Node):
    @staticmethod
    def fields():
        return ["cohort_code", "survival"]

class sample_to_patient(ontoweaver.Edge):
    @staticmethod
    def source_type():
        return sample

    @staticmethod
    def target_type():
        return patient

    @staticmethod
    def fields():
        return []


all = ontoweaver.All(sys.modules[__name__])
