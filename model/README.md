# ML
На данный момент эта чать кода развернута на вм. Архитектура как в примере бейзлайна [ссылка](http://176.123.167.46:8080):
## Запуск нашего решения

```cmd
python -m venv env
source env/bin/activate
pip install ./req.txt
```

## Запуск на 8080 порту
```cmd
uvicorn app:app --host 0.0.0.0 --port 8080 --reload
```

## Запросы

### Проверка работоспособности
```
curl -H "Content-type: application/json" -X GET http://176.123.167.46:8080
```

### Запрос в модель
```
curl -H "Content-type: application/json" -d '{"question": "Сколько в плейлисе может быть видео?"}' -X POST http://176.123.167.46:8080/predict
```
