Deps:

```
pip install -r requirements.txt
```

Usage:
```
python corpora.py --preprocess bible
python histogram.py --output-dir histograms/bible corpora/bible/*
python similarity.py --input unknown.txt --output unknown.json histograms/bible/*
python charts.py --input unknown.json
```
