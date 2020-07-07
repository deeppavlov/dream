from logging import getLogger
from typing import List
from itertools import chain
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from deeppavlov.core.common.registry import register
from deeppavlov.core.common.metrics_registry import register_metric
from deeppavlov.core.data.data_learning_iterator import DataLearningIterator
from deeppavlov.core.data.dataset_reader import DatasetReader
log = getLogger(__name__)

@register_metric('mean_squared_error')
def mse(y_true, y_predicted):
    """
    Calculates mean squared error.
    Args:
        y_true: list of true probs
        y_predicted: list of predicted peobs
    Returns:
        F1 score
    """
    #raise Exception(str(y_true[:5]))
    import _pickle as cPickle
    assert not (np.isnan(y_true).any())
    y_true = np.array(y_true)
    assert len(y_true.shape) == 2
    y_predicted = np.array(y_predicted)
    assert len(y_predicted.shape) == 2
    err = ((y_true-y_predicted)**2).sum()**0.5
    return err
@register('custom_classification_reader')
class BasicClassificationDatasetReader(DatasetReader):
    """
    Class provides reading dataset in .csv format
    """

    def read(self, data_path: str, url: str = None,
             format: str = "csv", class_sep: str = None,
             *args, **kwargs) -> dict:
        """
        Read dataset from data_path directory.
        Reading files are all data_types + extension
        (i.e for data_types=["train", "valid"] files "train.csv" and "valid.csv" form
        data_path will be read)

        Args:
            data_path: directory with files
            url: download data files if data_path not exists or empty
            format: extension of files. Set of Values: ``"csv", "json"``
            class_sep: string separator of labels in column with labels
            sep (str): delimeter for ``"csv"`` files. Default: None -> only one class per sample
            header (int): row number to use as the column names
            names (array): list of column names to use
            orient (str): indication of expected JSON string format
            lines (boolean): read the file as a json object per line. Default: ``False``

        Returns:
            dictionary with types from data_types.
            Each field of dictionary is a list of tuples (x_i, y_i)
        """
        data_types = ["train", "valid", "test"]

        train_file = kwargs.get('train', 'train.csv')

        if not Path(data_path, train_file).exists():
            if url is None:
                raise Exception(
                    "data path {} does not exist or is empty, and download url parameter not specified!".format(
                        data_path))
            log.info("Loading train data from {} to {}".format(url, data_path))
            download(source_url=url, dest_file_path=Path(data_path, train_file))

        data = {"train": [],
                "valid": [],
                "test": []}
        for data_type in data_types:
            file_name = kwargs.get(data_type, '{}.{}'.format(data_type, format))
            if file_name is None:
                continue

            file = Path(data_path).joinpath(file_name)
            if file.exists():
                if format == 'csv':
                    keys = ('sep', 'header', 'names')
                    options = {k: kwargs[k] for k in keys if k in kwargs}
                    df = pd.read_csv(file, **options)
                elif format == 'json':
                    keys = ('orient', 'lines')
                    options = {k: kwargs[k] for k in keys if k in kwargs}
                    df = pd.read_json(file, **options)
                else:
                    raise Exception('Unsupported file format: {}'.format(format))

                x = kwargs.get("x", "text")
                y = kwargs.get('y', 'labels')
                if isinstance(x, list):
                    print('LIST')
                    if class_sep is None:
                        #print('NOCLASSSEP')
                        #raise Exception()
                        # each sample is a tuple ("text", "label")
                        data[data_type] = [([row[x_] for x_ in x], str(row[y]))
                                           for _, row in df.iterrows()]
                    else:
                        #raise Exception('CLASSSEP')
                        # each sample is a tuple ("text", ["label", "label", ...])
                        data[data_type] = [([row[x_] for x_ in x], str(row[y]).split(class_sep))
                                           for _, row in df.iterrows()]
                else:
                    if class_sep is None:
                        #raise Exception('NOLISTNOCLASSEP')
                        # each sample is a tuple ("text", "label")
                        data[data_type] = [(row[x], str(row[y])) for _, row in df.iterrows()]
                    else:
                        #raise Exception('NOLISTCLASSEP')
                        # each sample is a tuple ("text", ["label", "label", ...])
                        try:
                            log.warning('Floats detected')
                            data[data_type] = [(row[x], [float(k) for k in str(row[y]).split(class_sep)]) for _, row in df.iterrows()]
                        except:
                            data[data_type] = [(row[x], str(row[y]).split(class_sep)) for _, row in df.iterrows()]
                        #raise Exception(data[data_type][0][1])
            else:
                log.warning("Cannot find {} file".format(file))
        #log.warning('getting exception')
        #raise Exception(str(data['train'][0]))
        return data
