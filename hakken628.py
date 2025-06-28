import streamlit as st
from collections import Counter
import random

# --- 乱数生成アルゴリズム定義 ---
class Xorshift:
    def __init__(self, seed):
        self.state = seed if seed != 0 else 1

    def next(self):
        x = self.state
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= (x >> 17)
        x ^= (x << 5) & 0xFFFFFFFF
        self.state = x & 0xFFFFFFFF
        return self.state

    def generate(self, count):
        return [self.next() for _ in range(count)]

def mersenne_twister(seed, count):
    random.seed(seed)
    return [random.randint(0, 100000) for _ in range(count)]

def middle_square(seed, count):
    n_digits = len(str(seed))
    value = seed
    result = []
    for _ in range(count):
        squared = value ** 2
        squared_str = str(squared).zfill(2 * n_digits)
        start = (len(squared_str) - n_digits) // 2
        middle_digits = int(squared_str[start:start + n_digits])
        result.append(middle_digits)
        value = middle_digits if middle_digits != 0 else seed + 1
    return result

def lcg(seed, count):
    m = 2**32
    a = 1664525
    c = 1013904223
    result = []
    x = seed
    for _ in range(count):
        x = (a * x + c) % m
        result.append(x)
    return result

def calculate_variance(numbers, n):
    mod_numbers = [x % n for x in numbers]
    counts = Counter(mod_numbers)
    all_counts = [counts.get(i, 0) for i in range(n)]
    expected = len(numbers) / n
    variance = sum((c - expected) ** 2 for c in all_counts) / n
    return variance, mod_numbers

@st.cache_data(show_spinner=False)
def find_best_seed_and_method(k, l, n):
    seed_range = range(0, 1000001, 100)
    count = int(k * l)
    best_variance = float('inf')
    best_method = None
    best_seed = None
    best_mod_result = None

    for method_name in ["Xorshift", "Mersenne Twister", "Middle Square", "LCG"]:
        for seed in seed_range:
            if method_name == "Xorshift":
                nums = Xorshift(seed).generate(count)
            elif method_name == "Mersenne Twister":
                nums = mersenne_twister(seed, count)
            elif method_name == "Middle Square":
                nums = middle_square(seed, count)
            elif method_name == "LCG":
                nums = lcg(seed, count)

            var, modded = calculate_variance(nums, n)

            if var < best_variance:
                best_variance = var
                best_method = method_name
                best_seed = seed
                best_mod_result = modded

    return best_method, best_seed, best_variance, best_mod_result

def run_app():
    st.title("🎲 年間指名表作成アプリ")

    k = st.number_input("年間授業回数", value=30, min_value=1)
    l = st.number_input("授業1回あたりの平均指名人数", value=5, min_value=1)
    n = st.number_input("クラス人数", value=40, min_value=1)

    name_input = st.text_area("✍️ 名前を改行区切りで入力（空欄箇所は自動生成します）", height=150)
    raw_names = [name.strip() for name in name_input.split("\n") if name.strip()]
    if len(raw_names) < n:
        raw_names += [f"名前{i+1}" for i in range(len(raw_names), n)]
    elif len(raw_names) > n:
        raw_names = raw_names[:n]
    names = raw_names
    st.write("👥 名前リスト:")
    st.write([f"{i+1} : {name}" for i, name in enumerate(names)])

    if st.button("📊 年間指名表を作成する"):
        with st.spinner("最適な指名表を探索中..."):
            best_method, best_seed, best_variance, best_mod_result = find_best_seed_and_method(k, l, n)

        st.session_state.named_pool = best_mod_result.copy()
        st.session_state.used_names = []
        st.session_state.names = names

        std_dev = best_variance ** 0.5
        expected = (k * l) / n
        min_calls = expected - std_dev
        max_calls = expected + std_dev

        st.success(
            f"✅ 乱数を生成するのに用いた式: {best_method}（seed={best_seed}）\n\n"
            f"📏 指名の偏り具合（標準偏差）: {std_dev:.2f}\n"
            f"📊 1人あたり {min_calls:.2f} 回 〜 {max_calls:.2f} 回 指名されます"
        )
        st.info("🎯 指名ボタンを押すと1人ずつランダムに指名されます")

    if st.button("🔄 全リセット"):
        for key in ["named_pool", "used_names", "names"]:
            if key in st.session_state:
                del st.session_state[key]
        st.experimental_rerun()

    if "named_pool" in st.session_state and "names" in st.session_state:
        pool = st.session_state.named_pool
        used = st.session_state.used_names
        names = st.session_state.names

        pool_counter = Counter(pool)
        used_counter = Counter(used)

        if st.button("🎯 指名！"):
            remaining_counter_before = pool_counter - used_counter
            remaining_before = list(remaining_counter_before.elements())

            if remaining_before:
                selected = random.choice(remaining_before)
                st.session_state.used_names.append(selected)

                st.info(f"🎉 指名された番号: {selected+1} （名前: {names[selected]}）🎉")
                st.markdown(f"<h1 style='text-align: center; color: green;'>{selected+1} : {names[selected]}</h1>", unsafe_allow_html=True)
            else:
                st.warning("✅ 全員の指名が完了しました！")

        used = st.session_state.used_names
        used_counter = Counter(used)
        remaining_counter = pool_counter - used_counter
        remaining = list(remaining_counter.elements())

        st.write(f"📌 残り指名可能人数: {len(remaining)} / {len(pool)}")

        if used:
            st.write(f"📋 指名済み一覧（{len(used)}人）:")
            named_list = [f"{i+1} : {names[i]}" for i in used]
            st.write(named_list)

if __name__ == "__main__":
    run_app()

