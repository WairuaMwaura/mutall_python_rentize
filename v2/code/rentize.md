# Nyumba

## Exporting python modules.

- To export this project's modules to a file ```rentize.txt``` in this case, use the code below.
```python
    pip freeze > rentize.txt
```

## Importing python modules

- To reuse this project as it was, make sure the ```rentize.txt``` exists in the current working directory. 
- If the file exists,run the command below to download the python modules using the code below.

```python
    pip install -r rentize.txt
```

