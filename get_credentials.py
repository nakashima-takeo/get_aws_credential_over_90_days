import boto3
import datetime
import csv
from datetime import timezone

# AWSのIAMサービスとの接続を設定
iam = boto3.client('iam')

# 現在の日付を取得
now = datetime.datetime.now(timezone.utc)

# 結果を保存するCSVファイルを開く
with open('unused_login_password.csv', mode='w', newline='') as file1, open('unused_access_key.csv', mode='w', newline='') as file2:
    writer1 = csv.writer(file1)
    writer2 = csv.writer(file2)
    # CSVのヘッダーを書き込む
    writer1.writerow(['UserName', 'LastAccessDate', 'Age'])
    writer2.writerow(['UserName', 'AccessKeyId', 'LastUsedDate'])

    # ページング処理で全IAMユーザーを取得
    paginator = iam.get_paginator('list_users')
    for page in paginator.paginate():
        # 90日を超えているアクセスキーを持つユーザーを見つける
        for user in page['Users']:
            # アカウントIDを取得
            acount_id = user['Arn'].split(':')[4]
            # アカウントIDが指定したものでなければスキップ
            if acount_id != '482842011168':
                continue
            user_name = user['UserName']
            # ユーザーのアクセスキーを取得
            access_keys = iam.list_access_keys(UserName=user_name)
            # ユーザーの詳細情報を取得
            user_details = iam.get_user(UserName=user_name)

            # ログインパスワードが90日以上未使用かどうかを確認
            # ログインパスワードが設定されているかを確認
            if 'PasswordLastUsed' in user_details['User']:
                last_used = user_details['User']['PasswordLastUsed']
                # 期限を計算（90日）
                age = now - last_used
                if age.days > 90:
                    # CSVファイルに書き込む(IAMユーザー、最終アクセス日時、経過日数)
                    writer1.writerow([user_name, last_used, age.days])

            # アクセスキーの最終使用日時から90日を超えているかを確認
            for key in access_keys['AccessKeyMetadata']:
                # アクセスキーが有効かを確認
                if key['Status'] != 'Active':
                    continue
                # アクセスキーの最終使用日を取得
                access_key_id = key['AccessKeyId']
                last_used_response = iam.get_access_key_last_used(AccessKeyId=access_key_id)
                last_used_info = last_used_response['AccessKeyLastUsed']
                # アクセスキーが使用されたことがある場合には、最終使用日を取得
                if 'LastUsedDate' in last_used_info:
                    last_used_date = last_used_info['LastUsedDate']
                    age = now - last_used_date
                    if age.days > 90:
                        # CSVファイルに書き込む
                        writer2.writerow([user_name, access_key_id, last_used_date])
                # 最終使用日が存在しない場合は、作成日が90日以上前の場合
                else:
                    create_date = key['CreateDate']
                    age = now - create_date
                    if age.days > 90:
                        # CSVファイルに書き込む
                        writer2.writerow([user_name, access_key_id, create_date])
            

# CSVファイルの保存が完了
print("CSVファイルに結果を保存しました。")
