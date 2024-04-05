# Тестовое задание на позицию “Full-stack разработчик” в компанию MYCEGO

Выполнено на Python 3.12

Использованы сторонние библиотеки:

* colorama
* Pillow
* requests

## Запуск

> python collage.py

Аргументом можно указать количество колонок в коллаже. По умолчанию количество колонок выбирается таким образом, чтобы сетка была как можно ближе к квадратной форме. 

> python collage.py 4

## Выполнение 

Первым делом производится запрос на содержание корневой папки в облаке. Папки, из которых берутся изображения, могут быть выбраны путём ввода строки, содержащей номера папок через запятую. 
Изображения кэшируются в оригинальном размере, таким образом при следующем запуске повторной загрузки не происходит.
Имеется конфигурация параметров коллажа: количество колонок, цвет фона, ширина ячеек, внешние отступы коллажа по отдельности, промежутки между ячейками.

Для получения коллажа как на примере (без сохранения порядка ячеек): указать количество колонок 4, выбрать папку "1388_12_Наклейки 3-D_3".