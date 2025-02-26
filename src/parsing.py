import statistics
import sys
import argparse


def read_log(filename):
    """로그 파일을 분석하여 청크 크기별 전송 시간 통계를 계산하는 함수"""
    result_dict = {}
    try:
        # UTF-8 인코딩으로 먼저 시도
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                if "DEBUG" in line:
                    transfer_time, chunk_size = line.split(" ")[-1].split(":")[-1].split("|")
                    if (result_dict.get(chunk_size)) is None:
                        result_dict[chunk_size] = []
                    result_dict[chunk_size].append(float(transfer_time))
    except UnicodeDecodeError:
        # UTF-8로 실패하면 다른 인코딩 시도

        with open(filename, 'r', encoding='euc-kr') as f:
            for line in f:
                if "DEBUG" in line:
                    transfer_time, chunk_size = line.split(" ")[-1].split(":")[-1].split("|")
                    if (result_dict.get(chunk_size)) is None:
                        result_dict[chunk_size] = []
                    result_dict[chunk_size].append(float(transfer_time))

    except FileNotFoundError:
        print(f"오류: 파일 '{filename}'을 찾을 수 없습니다.")
        return None
    except Exception as e:
        print(f"오류 발생: {e}")
        return None

    # 각 result_dict의 value의 최대 최소 평균 중간값 구하기
    print(f"{'chunk_size':^10} | {'min':^10} | {'max':^10} | {'avg':^10} | {'med':^10} | {'std':^10}")
    print(f"{'-' * 60}")

    for chunk_size, times in sorted(result_dict.items(), key=lambda x: float(x[0])):
        if times:
            min_time = min(times)
            max_time = max(times)
            avg_time = sum(times) / len(times)
            median_time = statistics.median(times)
            std_dev_time = statistics.stdev(times)

            print(
                f"{chunk_size:^10} | {min_time:^10.4f} | {max_time:^10.4f} | {avg_time:^10.4f} | {median_time:^10.4f} | {std_dev_time:^10.4f}")

    return result_dict


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="로그 파일에서 청크 크기별 전송 시간 통계 분석")
    parser.add_argument("-f", "--file", required=True, help="분석할 로그 파일 경로")
    args = parser.parse_args()

    print(f"{args.file} 파일 분석 중...")
    result = read_log(args.file)
    print(result)

    if result:
        print("\n분석 완료!")
        # 여기에 결과를 이용한 추가 작업 가능
        # 예: 그래프 생성, 파일 저장 등
    else:
        print("분석 실패. 프로그램을 종료합니다.")
        sys.exit(1)