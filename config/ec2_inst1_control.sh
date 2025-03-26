#!/bin/bash  
#これで権限を付与してからpushすること。
#chmod +x ec2_core8_instance_control.sh

# インスタンスID（AWS EC2のインスタンスIDを指定します）
INSTANCE_ID="i-0e8a52d187fcd644e"

# ユーザーからの引数（start、stop、list）を受け取る
ACTION=$1  # このスクリプトの実行時に渡された最初の引数を取得します。

# 条件分岐でユーザーの選択に応じた処理を実行
if [ "$ACTION" == "start" ]; then
    echo "Starting instance $INSTANCE_ID ..."
    aws ec2 start-instances --instance-ids $INSTANCE_ID --output json

elif [ "$ACTION" == "stop" ]; then
    echo "Stopping instance $INSTANCE_ID ..."
    aws ec2 stop-instances --instance-ids $INSTANCE_ID --output json

elif [ "$ACTION" == "list" ]; then
    echo "Listing all instances with their state ..."
    aws ec2 describe-instances \
        --query "Reservations[].Instances[].[
            InstanceId, 
            State.Name, 
            Tags[?Key=='Name']|[0].Value
        ]" \
        --output json
else
    echo "Usage: $0 {start|stop|list}"  # 正しい使い方を案内
fi  # 条件分岐の終了