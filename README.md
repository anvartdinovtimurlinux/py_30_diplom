# Задание на дипломный проект «Шпионские игры» курса «Python: программирование на каждый день и сверхбыстрое прототипирование»
Программа выводит список групп в ВК в которых состоит пользователь, но не состоит никто из его друзей

Программа запускается из командной строки `python3 get_groups_without_friends.py`

При запуске можно указать необязательные ключи:
* -n, --name - никнейм пользователя или его ID;
* -f, --file - путь к файлу, в который запишется результат работы программы;

Пример запуска:
`python3 get_groups_without_friends.py --name eshmargunov -f result.txt`

Если не будет указан ключ --name, программа запустится в интерактивном режиме


## Зависимости
Программа использует внешние библиотеки
* [requests](https://github.com/psf/requests)
* [progress](https://github.com/verigak/progress/)
