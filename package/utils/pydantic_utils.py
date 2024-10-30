import csv
import io
import json


def dump_csv(*models) -> str:
    """Serialize the given model(s) to a CSV string."""
    data = [model.model_dump() for model in models]

    output = io.StringIO()
    writer = csv.writer(output)
    headers = data[0].keys()
    writer.writerow(headers)

    for entry in data:
        row = []
        for key in headers:
            value = entry[key]
            if value is None:
                row.append("null")
            elif isinstance(value, (dict, list)):
                # TODO Improve null handling. None (NoneType) must be replaced with null,
                # but "None" (string) must be kept as is, e.g
                # Input: ["None", None]
                # Output: "[""None"", null]"
                row.append(json.dumps(value, default=str).replace("None", "null"))
            else:
                row.append(value)
        writer.writerow(row)

    return output.getvalue().strip()
