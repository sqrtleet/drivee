import folium
import webbrowser
import osmnx as ox
from loguru import logger

import config


def get_distances(graph, start, end, arr):
    """
    Возвращает отсортированный по дистанции массив заказов

    :param graph: Граф osmnx
    :param start: Стартовая точка поездки
    :param end: Конечная точка поездки
    :param arr: Массив с координатами заказов
    """

    # Находим ближайшие вершины
    # Принимает граф, долготу и широту
    orig_node = ox.nearest_nodes(graph, start[1], start[0])
    dest_node = ox.nearest_nodes(graph, end[1], end[0])
    path0 = ox.shortest_path(graph, orig_node, dest_node)
    full_distance = calculate_distance(graph, path0)
    logger.info("Кратчайшая дистанция от А до Б составит: {:.2f} м.".format(full_distance))

    # Создаем список, в котором будем хранить пути
    total_paths = []
    path1_paths = []
    path2_paths = []
    path_distances = []
    suitable_orders = []

    for i, el in enumerate(arr):
        # Находим ближайший узел к началу заказа
        point1_node = ox.nearest_nodes(graph, arr[i][1], arr[i][0])
        # Находим ближайший узел к концу заказа
        point2_node = ox.nearest_nodes(graph, arr[i][3], arr[i][2])

        # Находим путь от точки А до начала заказа
        path1 = ox.shortest_path(graph, orig_node, point1_node, weight=config.optimizer)
        # Находим путь от начала заказа до конца заказа
        path2 = ox.shortest_path(
            graph, point1_node, point2_node, weight=config.optimizer
        )
        # Находим путь от конца заказа до точки Б
        path3 = ox.shortest_path(graph, point2_node, dest_node, weight=config.optimizer)
        # Объединяем найденные пути
        total_path = path1 + path2 + path3

        # Вычисляем длину пути от точки А до начала заказа
        path1_distance = calculate_distance(graph, path1)
        # Вычисляем длину пути от начала заказа до конца заказа
        path2_distance = calculate_distance(graph, path2)

        total_path_distance = calculate_distance(graph, total_path)

        if total_path_distance < full_distance * config.max_length_factor:
            total_paths.append(total_path)
            path1_paths.append(path1)
            path2_paths.append(path2)
            path_distances.append(
                (i, (path1_distance, path2_distance, total_path_distance))
            )
            suitable_orders.append(el)
        else:
            logger.info(
                "Дистанция маршрута заказа №{} больше ограничения: {:.2f} м. > {:.2f} м.".format(
                    i + 1, calculate_distance(graph, total_path), full_distance * config.max_length_factor
                )
            )

    # Сортировка массива дистанций по расстоянию от начала заказа до конца заказа
    sorted_distances = sorted(path_distances, key=lambda item: item[1][2])

    return suitable_orders, total_paths, sorted_distances


def calculate_distance(graph, path):
    """
    Вычисляет дистанцию между двумя узлами графа на основе координат узлов.
    :param graph: Граф osmnx
    :param path: Массив вершин графа
    :return: Возвращает дистанцию в метрах
    """
    distance = sum(
        ox.distance.great_circle_vec(
            graph.nodes[node1]["y"],
            graph.nodes[node1]["x"],
            graph.nodes[node2]["y"],
            graph.nodes[node2]["x"],
        )
        for node1, node2 in zip(path[:-1], path[1:])
    )
    return distance


def plot_route_folium(graph, start, end, arr, total_paths, path_distances):
    """
    Отрисовывает карту с заказами
    :param graph: Граф osmnx
    :param start: Стартовая точка поездки
    :param end: Конечная точка поездки
    :param arr: Заказы
    :param total_paths: Вершины графа путей
    :param path_distances: Дистанции путей заказов в метрах
    """
    # Создаем карту
    m = folium.Map(location=(start[0], start[1]), zoom_start=15)

    # Добавляем маркеры для начальной и конечной точек
    folium.Marker([start[0], start[1]], tooltip="Start").add_to(m)
    folium.Marker([end[0], end[1]], tooltip="End").add_to(m)

    # Добавляем маркеры для промежуточных точек
    for i, point in enumerate(arr):
        k, dist = path_distances[i]
        folium.Marker(
            [point[0], point[1]],
            popup="Расстояние до заказа: {:.2f} м.\nРасстояние заказа: {:.2f} м.\nРасстояние до точки Б: {:.2f} м.".format(
                dist[0], dist[1], dist[2]
            ),
            icon=folium.Icon(config.colors[i]),
            tooltip="Заказ №{} начало".format(k+1),
        ).add_to(m)
        folium.Marker(
            [point[2], point[3]],
            icon=folium.Icon(config.colors[i], icon=""),
            tooltip="Заказ №{} конец".format(k),
        ).add_to(m)

    # Отображаем маршруты
    for i, p in enumerate(total_paths):
        folium.PolyLine(
            locations=[(graph.nodes[n]["y"], graph.nodes[n]["x"]) for n in p],
            weight=6,
            color=config.colors[i],
            opacity=0.7,
            line_cap="round",
        ).add_to(m)
    # Отобразить карту
    m.save(config.file_name)
    webbrowser.open(config.file_name)


def main():
    # Широта и долгота
    start = (61.980837, 129.653896)
    end = (62.009191, 129.677320)
    arr = [
        (62.005583, 129.681952, 62.009347, 129.680248),
        (61.985420, 129.677769, 61.992816, 129.685136),
        (61.999908, 129.690471, 62.010227, 129.682359),
        (62.011391, 129.695186, 62.008179, 129.683365),
        (61.999726, 129.71305, 62.00773, 129.676551),
    ]
    suitable_orders, total_paths, path_distances = get_distances(config.graph, start, end, arr)

    plot_route_folium(config.graph, start, end, suitable_orders, total_paths, path_distances)
    logger.info("Рекомендуемые заказы по длине маршрута:")
    for i, distance in path_distances:
        logger.info(
            "Дистанция от начала маршрута до вашей конечной точки при взятии заказа №{} составит: {:.2f} м.".format(
                i + 1, distance[2]
            )
        )


if __name__ == "__main__":
    main()
