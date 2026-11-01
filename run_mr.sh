#!/bin/bash
MAX_ITER=${1:-2000}
STREAM=$(find $HADOOP_HOME -name 'hadoop-streaming-*.jar' | head -1)
hdfs dfs -rm -r -f /dijkstra > /dev/null 2>&1
hdfs dfs -mkdir -p /dijkstra/iter0
hdfs dfs -put graph_mr.txt /dijkstra/iter0/
START=$(date +%s)
i=0
while [ $i -lt $MAX_ITER ]; do
  hadoop jar "$STREAM" -D mapreduce.job.reduces=2 -files dj_mapper,dj_reducer \
    -mapper ./dj_mapper -reducer ./dj_reducer \
    -input /dijkstra/iter$i -output /dijkstra/iter$((i+1)) > iter.log 2>&1
  upd=$(grep -o 'Updated=[0-9]*' iter.log | head -1 | cut -d= -f2)
  upd=${upd:-0}
  i=$((i+1))
  echo "Vong $i: cap nhat $upd node"
  hdfs dfs -rm -r -skipTrash /dijkstra/iter$((i-1)) > /dev/null 2>&1
  [ "$upd" -eq 0 ] && break
done
END=$(date +%s)
echo "Tong so vong: $i, thoi gian: $((END-START)) giay"
echo $i > final_iter.txt
bash run_mr.sh - đừng nên chạy với dữ liệu lớn vì nó tốn vài tiếng