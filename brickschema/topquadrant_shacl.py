import subprocess
import platform
import pkgutil
import tempfile
import rdflib
from rdflib import OWL, SH
from pathlib import Path


MAX_ITERATIONS = 20


def infer(data_graph: rdflib.Graph, ontologies: rdflib.Graph):
    # remove imports
    data_graph.remove((None, OWL.imports, None))

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        # Define the target path within the temporary directory
        target_file_path = temp_dir_path / "data.ttl"

        combined = data_graph + ontologies
        combined.serialize(target_file_path, format="ttl")

        # Run inference in a loop until the size of the data_graph doesn't change or we have run at least two iterations
        previous_size = 0
        current_size = len(data_graph)
        iteration_count = 0

        # set the SHACL_HOME environment variable to point to the shacl-1.4.2 directory
        # so that the shaclinfer.sh script can find the shacl.jar file
        env = {"SHACL_HOME": str(Path(__file__).parent / "topquadrant_shacl")}
        while iteration_count < MAX_ITERATIONS and previous_size != current_size:
            iteration_count += 1
            # get the shacl-1.4.2/bin/shaclinfer.sh script from brickschema.bin in this package
            # using pkgutil. If using *nix, use .sh; else if on windows use .bat
            if platform.system() == "Windows":
                script = [
                    str(Path(__file__).parent / "topquadrant_shacl/bin/shaclinfer.bat")
                ]
            else:
                script = [
                    "/bin/sh",
                    str(Path(__file__).parent / "topquadrant_shacl/bin/shaclinfer.sh"),
                ]

            try:
                print(f"Running {script} -datafile {target_file_path}")
                output = subprocess.check_output(
                    [*script, "-datafile", target_file_path],
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    env=env,
                )
            except subprocess.CalledProcessError as e:
                output = e.output  # Capture the output of the failed subprocess
            # Write logs to a file in the temporary directory (or the desired location)
            inferred_file_path = temp_dir_path / "inferred.ttl"
            with open(inferred_file_path, "w") as f:
                for line in output.splitlines():
                    if "::" not in line:
                        f.write(f"{line}\n")
            inferred_triples = rdflib.Graph()
            inferred_triples.parse(inferred_file_path, format="turtle")
            print(f"Got {len(inferred_triples)} inferred triples")

            if len(inferred_triples) == 0:
                break

            # add inferred triples to the data graph, then serialize it
            data_graph += inferred_triples
            combined = data_graph + ontologies
            combined.serialize(target_file_path, format="ttl")

            # Update the sizes for the next iteration
            previous_size = current_size
            current_size = len(data_graph)
        return data_graph


def validate(data_graph: rdflib.Graph):
    # remove imports
    data_graph.remove((None, OWL.imports, None))

    # set the SHACL_HOME environment variable to point to the shacl-1.4.2 directory
    # so that the shaclinfer.sh script can find the shacl.jar file
    env = {"SHACL_HOME": str(Path(__file__).parent / "topquadrant_shacl")}
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        # Define the target path within the temporary directory
        target_file_path = temp_dir_path / "data.ttl"

        data_graph.serialize(target_file_path, format="ttl")

        # Run inference in a loop until the size of the data_graph doesn't change or we have run at least two iterations
        previous_size = 0
        current_size = len(data_graph)
        iteration_count = 0

        while iteration_count < MAX_ITERATIONS or previous_size != current_size:
            iteration_count += 1
            # get the shacl-1.4.2/bin/shaclinfer.sh script from brickschema.bin in this package
            # using pkgutil. If using *nix, use .sh; else if on windows use .bat
            if platform.system() == "Windows":
                script = [
                    str(Path(__file__).parent / "topquadrant_shacl/bin/shaclinfer.bat")
                ]
            else:
                script = [
                    "/bin/sh",
                    str(Path(__file__).parent / "topquadrant_shacl/bin/shaclinfer.sh"),
                ]
            # check if we need to use .bat

            try:
                print(f"Running {script} -datafile {target_file_path}")
                output = subprocess.check_output(
                    [*script, "-datafile", target_file_path],
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    env=env,
                )
            except subprocess.CalledProcessError as e:
                output = e.output  # Capture the output of the failed subprocess
            # Write logs to a file in the temporary directory (or the desired location)
            inferred_file_path = temp_dir_path / "inferred.ttl"
            with open(inferred_file_path, "w") as f:
                for line in output.splitlines():
                    if "::" not in line:
                        f.write(f"{line}\n")
            inferred_triples = rdflib.Graph()
            inferred_triples.parse(inferred_file_path, format="turtle")
            print(f"Got {len(inferred_triples)} inferred triples")

            # add inferred triples to the data graph, then serialize it
            data_graph += inferred_triples
            data_graph.serialize(target_file_path, format="ttl")

            # Update the sizes for the next iteration
            previous_size = current_size
            current_size = len(data_graph)

        # get the shacl-1.4.2/bin/shaclvalidate.sh script from the same directory
        # as this file
        if platform.system() == "Windows":
            script = [
                str(Path(__file__).parent / "topquadrant_shacl/bin/shaclvalidate.bat")
            ]
        else:
            script = [
                "/bin/sh",
                str(Path(__file__).parent / "topquadrant_shacl/bin/shaclvalidate.sh"),
            ]
        try:
            print(f"Running {script} -datafile {target_file_path}")
            output = subprocess.check_output(
                [*script, "-datafile", target_file_path],
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                env=env,
            )
        except subprocess.CalledProcessError as e:
            output = e.output  # Capture the output of the failed subprocess

        # Write logs to a file in the temporary directory (or the desired location)
        report_file_path = temp_dir_path / "report.ttl"
        with open(report_file_path, "w") as f:
            for line in output.splitlines():
                if "::" not in line:  # filter out log output
                    f.write(f"{line}\n")

        report_g = rdflib.Graph()
        report_g.parse(report_file_path, format="turtle")

        # check if there are any sh:resultSeverity sh:Violation predicate/object pairs
        has_violation = len(
            list(report_g.subjects(predicate=SH.resultSeverity, object=SH.Violation))
        )
        conforms = len(
            list(report_g.subjects(predicate=SH.conforms, object=rdflib.Literal(True)))
        )
        validates = not has_violation or conforms

        return validates, report_g, str(report_g.serialize(format="turtle"))
