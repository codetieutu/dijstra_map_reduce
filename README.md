# Dijkstra song song trên MapReduce (dữ liệu OpenStreetMap Đà Nẵng)

Dự án tính đường đi ngắn nhất (bài toán SSSP) trên mạng lưới đường bộ Đà Nẵng lấy từ OpenStreetMap.
Có hai bản cài đặt để so sánh:

- **Tuần tự:** Dijkstra với `priority_queue` (C++).
- **Song song:** thư giãn cạnh đồng bộ theo vòng trên Hadoop MapReduce (Hadoop Streaming, mapper và reducer viết bằng C++). Mỗi vòng là một job; dừng khi không còn nút nào được cải thiện.

## 1. Yêu cầu môi trường

|   Thành phần    |          Phiên bản đã dùng                        |
|-----------------|---------------------------------------------------|
| Hệ điều hành    | Ubuntu 24.04 trên WSL2 (Windows 11)               |
| Hadoop          | 3.4.1, chế độ giả phân tán (một máy)              |
| Trình biên dịch | g++ hỗ trợ C++17                                  |
| Python          | 3.x, chỉ dùng thư viện chuẩn (không cần cài thêm) |
| Mạng            | Cần khi tải dữ liệu từ Overpass API lần đầu       |

Biến môi trường `HADOOP_HOME` phải được đặt (ví dụ `/home/<user>/hadoop`).

## 2. Cấu trúc thư mục

```
project/
├── prep_osm.py          # tải OSM, dựng đồ thị, xuất nodes.csv và edges.txt
├── nearest.py           # tìm nút gần nhất với một tọa độ
├── make_graph_mr.py     # tạo graph_mr.txt cho MapReduce theo nút nguồn
├── dj_mapper.cpp        # mapper
├── dj_reducer.cpp       # reducer
├── dijkstra_seq.cpp     # bản tuần tự, ghi seq_dist.txt và path.txt
├── run_mr.sh            # chạy vòng lặp MapReduce đến khi hội tụ
├── run_mr_test.sh       # đo thời gian với số reducer và số vòng tùy chọn
└── small/               # bản sao các tệp trên, dùng cho đồ thị nhỏ (BBOX nhỏ)
```

Các tệp sinh ra khi chạy: `danang.json` (dữ liệu OSM thô), `nodes.csv`, `edges.txt`, `graph_mr.txt`, `seq_dist.txt`, `path.txt`, `mr_dist.txt`, `final_iter.txt`, `iter.log`.

## 3. Hướng dẫn nhanh

### 3.1. Bật Hadoop (mỗi lần mở lại WSL)

```bash
sudo service ssh start
start-dfs.sh
start-yarn.sh
jps        # phải thấy đủ 5 daemon: NameNode, DataNode, SecondaryNameNode, ResourceManager, NodeManager
```

### 3.2. Biên dịch

```bash
g++ -O2 -std=c++17 -o dijkstra_seq dijkstra_seq.cpp
g++ -O2 -std=c++17 -o dj_mapper dj_mapper.cpp
g++ -O2 -std=c++17 -o dj_reducer dj_reducer.cpp
chmod +x dj_mapper dj_reducer
```

### 3.3. Tạo đồ thị từ OpenStreetMap

Khung tọa độ đặt ở biến `BBOX = (nam, tây, bắc, đông)` đầu tệp `prep_osm.py`. Sau đó:

```bash
python3 prep_osm.py 0
```

Đối số của `prep_osm.py` là **mã nút nguồn** (một số nguyên), không phải tọa độ. Lệnh này tạo `nodes.csv` và `edges.txt`. Lần đầu tải dữ liệu mất 1 đến 2 phút; các lần sau dùng lại `danang.json`.

### 3.4. Chọn nút nguồn và đích

```bash
python3 nearest.py 16.0619 108.1591      # hai số cách nhau bằng dấu cách, không có dấu phẩy
```

Kết quả dạng `node 2367 tại 16.0623303 108.1595277`. Số sau chữ `node` là mã nút. Làm tương tự cho điểm đích.

### 3.5. Chạy bản tuần tự (kết quả chuẩn)

```bash
./dijkstra_seq <SRC> <DST>
```

In ra khoảng cách (mét), số nút trên đường đi và thời gian chạy. Ghi `seq_dist.txt` (khoảng cách tới mọi nút, `-1` nếu không tới được) và `path.txt`.

### 3.6. Chạy bản MapReduce

```bash
python3 make_graph_mr.py <SRC>     # tạo graph_mr.txt
bash run_mr.sh                     # chạy đến khi hội tụ
bash run_mr.sh 5                   # hoặc giới hạn 5 vòng để chạy thử
```

Cuối cùng in tổng số vòng và thời gian, ghi số vòng vào `final_iter.txt`.

### 3.7. Đối chiếu hai bản

```bash
I=$(cat final_iter.txt)
hdfs dfs -cat /dijkstra/iter$I/part-* | awk -F'\t' '{split($2,a,"|"); d=(a[2]==2147483647)?-1:a[2]; print $1"\t"d}' | sort -n > mr_dist.txt
sort -n seq_dist.txt | diff - mr_dist.txt && echo "KHOP HOAN TOAN"
```

### 3.8. Đo thời gian theo số reducer

```bash
bash run_mr_test.sh <so_reducer> <so_vong>     # ví dụ: bash run_mr_test.sh 2 10
```

Script này tắt chế độ uber ở mọi lần chạy để so sánh công bằng giữa các số reducer.

## 4. Định dạng dữ liệu

- `edges.txt`: mỗi dòng `u v w` (nút đi, nút đến, trọng số tính bằng mét, số nguyên không nhỏ hơn 1). Đồ thị có hướng.
- `nodes.csv`: `id,osm_id,lat,lon`.
- `graph_mr.txt`: mỗi nút một dòng, dạng `u<TAB>N|d|prev|adj`, trong đó `d` là khoảng cách hiện tại (`INF = 2147483647` nếu chưa biết), `prev` là nút đứng trước (`-1` nếu chưa có), `adj` là `v1:w1,v2:w2,...`.
- Thông điệp trung gian giữa mapper và reducer: `v<TAB>M|d'|u`.


1. **Mã nút chỉ có nghĩa trong từng tập dữ liệu.** Mỗi lần chạy `prep_osm.py` với `BBOX` khác, mã nút được đánh lại từ 0. Mã nguồn và đích tìm ở tập này không dùng được cho tập khác. Hãy chạy lại `nearest.py` mỗi khi đổi tập dữ liệu.
2. **Điểm nguồn và đích phải nằm trong `BBOX`.** Ngoài khung không có dữ liệu đường; `nearest.py` sẽ trả về nút ở mép khung, cách xa tọa độ bạn nhập. Hãy so sánh tọa độ in ra với tọa độ đã nhập.
3. **Có thể không có đường đi theo đúng chiều** do đường một chiều. Nếu `dijkstra_seq` báo không có đường đi, thử đổi chỗ nguồn và đích, chọn điểm khác, hoặc đặt `HONOR_ONEWAY = False` trong `prep_osm.py` rồi tạo lại dữ liệu.
4. **Không chạy tập lớn đến khi hội tụ.** Số vòng xấp xỉ số cạnh của đường đi ngắn nhất dài nhất, mỗi vòng mất khoảng 25 đến 30 giây, nên tập lớn có thể mất nhiều giờ. Hãy chạy thử với `bash run_mr.sh 5`, còn việc chạy đến khi hội tụ làm trên tập nhỏ.
5. **Bản MapReduce chậm hơn bản tuần tự rất nhiều** ở quy mô này. Đây là kết quả bình thường, do số vòng lớn và chi phí khởi động mỗi job, không phải lỗi chương trình.
6. **`prep_osm.py` cũng ghi `graph.txt`** theo định dạng cũ. Tệp này không dùng cho MapReduce; hãy dùng `graph_mr.txt` do `make_graph_mr.py` tạo.
7. **`run_mr.sh` xóa thư mục `/dijkstra` trên HDFS** mỗi lần bắt đầu, và xóa thư mục kết quả của vòng cũ sau mỗi vòng. Đừng lưu dữ liệu khác ở đó.
8. **`run_mr.sh` dùng 1 reducer và bật chế độ uber** (chạy tác vụ trong một JVM) để giảm chi phí mỗi vòng. Với nhiều reducer, dùng `run_mr_test.sh`.
9. **Khi sửa tệp bằng `nano`, thụt lề bằng dấu cách, không bấm Tab.** Trộn Tab với dấu cách làm Python báo `TabError`.
10. Dữ liệu bản đồ thuộc về cộng tác viên OpenStreetMap, giấy phép ODbL. Khi công bố cần ghi nguồn: © OpenStreetMap contributors.

## 7. Xử lý lỗi thường gặp


| `ssh: connect to host localhost port 22: Connection refused` khi `start-dfs.sh` | Dịch vụ SSH trong WSL chưa chạy | `sudo service ssh start`, rồi `start-dfs.sh` và `start-yarn.sh` |
| `jps` thiếu NameNode hoặc DataNode | Hadoop khởi động chưa đầy đủ | `stop-yarn.sh`, `stop-dfs.sh`, bật SSH rồi khởi động lại |
| `ClassNotFoundException: -D` | Biến `STREAM` trỏ nhầm sang jar chứa mã nguồn (`...-test-sources.jar`) | Dùng jar trong `$HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar` |
| Chạy vài giây và báo cập nhật 0 node ở vòng 1 | Job lỗi chứ không phải đã hội tụ | Đọc `tail -30 iter.log`; kiểm tra `HADOOP_HOME`, safe mode (`hdfs dfsadmin -safemode get`), sự tồn tại của `dj_mapper`, `dj_reducer`, `graph_mr.txt` |
| `HTTP Error 502: Bad Gateway` khi tải từ Overpass | Máy chủ Overpass quá tải | Chạy lại sau ít phút, hoặc copy `danang.json` đã có vào thư mục và cắt theo `BBOX`; có thể thử máy chủ dự phòng `https://overpass.kumi.systems/api/interpreter` |
| `ValueError: invalid literal for int()` khi chạy `prep_osm.py` | Truyền chữ hoặc tọa độ thay vì mã nút | Dùng một số nguyên làm mã nút nguồn |
| `FileNotFoundError: nodes.csv` | Chưa chạy `prep_osm.py` trong thư mục hiện tại | Chạy `python3 prep_osm.py 0` trước |
| `TabError: inconsistent use of tabs and spaces` | Lẫn Tab và dấu cách trong tệp Python | Đổi toàn bộ Tab thành 4 dấu cách |
| `diff` báo lệch giữa `seq_dist.txt` và `mr_dist.txt` | Hai bản chạy trên đồ thị hoặc nguồn khác nhau | Chạy lại `dijkstra_seq` trên đúng đồ thị và nguồn đã dùng cho `make_graph_mr.py` |