from io import BytesIO
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


DATA_PATH = Path("data/Online Retail.xlsx")
DATA_URL = "https://archive.ics.uci.edu/static/public/352/online+retail.zip"


def download_data(path: Path) -> None:
    """Скачивает исходные данные из UCI при первом запуске проекта."""
    print("Исходный файл не найден. Скачиваю набор данных из UCI...")
    path.parent.mkdir(exist_ok=True)

    with urlopen(DATA_URL) as response:
        archive = ZipFile(BytesIO(response.read()))
        xlsx_file = next(name for name in archive.namelist() if name.endswith(".xlsx"))
        with archive.open(xlsx_file) as source, path.open("wb") as target:
            target.write(source.read())

    print(f"Данные сохранены в {path}")


def load_and_prepare_data(path: Path) -> pd.DataFrame:
    """Загружает данные и оставляет только корректные продажи."""
    if not path.exists():
        download_data(path)

    df = pd.read_excel(path)
    df.columns = df.columns.str.strip()

    # Отменённые заказы начинаются с буквы C, а отрицательные значения не являются продажами.
    df = df[~df["InvoiceNo"].astype(str).str.startswith("C")].copy()
    df = df[(df["Quantity"] > 0) & (df["UnitPrice"] > 0)].copy()
    df = df.dropna(subset=["CustomerID", "Description"])

    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["Revenue"] = df["Quantity"] * df["UnitPrice"]
    df["Month"] = df["InvoiceDate"].dt.to_period("M").astype(str)
    return df


def main() -> None:
    sns.set_theme(style="whitegrid")
    df = load_and_prepare_data(DATA_PATH)

    print(f"Строк после очистки: {len(df):,}")
    print(f"Выручка: £{df['Revenue'].sum():,.2f}")
    print(f"Уникальных клиентов: {df['CustomerID'].nunique():,}")

    top_countries = (
        df.groupby("Country", as_index=False)["Revenue"]
        .sum()
        .sort_values("Revenue", ascending=False)
        .head(10)
    )
    print("\nТоп-10 стран по выручке:\n", top_countries.to_string(index=False))

    monthly_revenue = df.groupby("Month", as_index=False)["Revenue"].sum()
    plt.figure(figsize=(12, 6))
    sns.lineplot(data=monthly_revenue, x="Month", y="Revenue", marker="o")
    plt.title("Динамика выручки по месяцам")
    plt.xlabel("Месяц")
    plt.ylabel("Выручка, £")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("monthly_revenue.png", dpi=150)
    print("\nГрафик сохранён в файл monthly_revenue.png")


if __name__ == "__main__":
    main()
