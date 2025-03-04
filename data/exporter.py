from math import e
import pandas as pd
from data_models.electrode import Electrode
from config.mappings import ElectrodesFileMapping


def export_electrodes_to_file(electrodes: list[Electrode], filename: str) -> None:
    def export_csv(suffix: str = ""):
        dfs = []
        for electrode in electrodes:
            dfs.append(electrode.df)
        df = pd.concat(dfs)
        df.to_csv(filename + suffix, index=False)

    extension = filename.split(".")[-1]

    match extension:
        case "csv":
            export_csv()
        case "ced":
            with open(filename, "w") as f:
                # write the header
                f.write(
                    (
                        f"{ElectrodesFileMapping.CED_LABEL}\t"
                        f"{ElectrodesFileMapping.CED_X}\t"
                        f"{ElectrodesFileMapping.CED_Y}\t"
                        f"{ElectrodesFileMapping.CED_Z}\n"
                    )
                )

                # write the electrodes
                for electrode in electrodes:
                    f.write(
                        (
                            f"{electrode.label}\t"
                            f"{electrode.coordinates[0]}\t"
                            f"{electrode.coordinates[1]}\t"
                            f"{electrode.coordinates[2]}\n"
                        )
                    )
        case _:
            export_csv(suffix=".csv")
