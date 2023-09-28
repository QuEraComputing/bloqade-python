from bloqade.builder.base import Builder


class BraketService(Builder):
    @property
    def braket(self):
        """
        - Specify the Braket backend
            - This allows you to access the AWS Braket local emulator OR go submit things to QuEra hardware on AWS Braket service.
        - Possible Next Steps are:
            - |_ `...braket.aquila()`: target submission to the QuEra Aquila QPU
            - |_ `...braket.local_emulator()`: target submission to the Braket local emulator
        """
        return BraketDeviceRoute(self)


class BraketDeviceRoute(Builder):
    def aquila(self):
        """
        - Specify QuEra's Aquila QPU on Braket to submit your program to.
        - The number of shots you specify in the subsequent `.run` method will either:
            - dictate the number of times your program is run
            - dictate the number of times per parameter your program is run if you have a
              variable with batch assignments/intend to conduct a parameter sweep
        - Possible next steps are:
            - |_ `...aquila().run(shots)`: To submit to hardware and WAIT for results (blocking)
            - |_ `...aquila().run_async(shots)`: To submit to hardware and immediately allow for other operations to occur
        """
        return self.parse().braket.aquila()

    def local_emulator(self):
        """
        - Specify the Braket local emulator to submit your program to.
        - The number of shots you specify in the subsequent `.run` method will either:
            - dictate the number of times your program is run
            - dictate the number of times per parameter your program is run if you have a
              variable with batch assignments/intend to conduct a parameter sweep
        - Possible next steps are:
            - |_ `...local_emulator().run(shots)`: to submit to the emulator and await results

        """
        return self.parse().braket.local_emulator()
