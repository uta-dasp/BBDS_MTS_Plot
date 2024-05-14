import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk
import matplotlib

# default font selection

matplotlib.rcParams['font.family'] = "Arial"
matplotlib.rcParams['font.weight'] = 'bold'
matplotlib.rcParams['font.size'] = 14
matplotlib.rcParams['figure.figsize'] = (8, 6)
# Create the main Tkinter window
root = tk.Tk()
root.title("MTS_BBDS_GUI_v2024")

# Variables to store the file paths

# global mtsnp, bbdsnp

thickness = tk.DoubleVar()
thickness.set(1.83)
gage_length = tk.DoubleVar()
gage_length.set(152)
width = tk.DoubleVar()
width.set(19)
interval_time = tk.DoubleVar()
interval_time.set(3)
dwell_time = tk.DoubleVar()
dwell_time.set(30)


class ConsoleRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, output):
        self.text_widget.insert(tk.END, output)
        self.text_widget.see(tk.END)


def select_file():
    filepath = filedialog.askopenfilename(
        title="Select Sample File",
        filetypes=(("Text files", "*.txt"), ("Text Files", "*.TXT")),
    )
    df = pd.read_csv(filepath, skiprows=2, delimiter="\t", header=None)
    return df


df = select_file()
#print((df.iloc[0, 3]).strip())


def button_clicked(button_text):
    print(f"Button {button_text} clicked!")


def norm_on():
    global norm
    norm_on_button.config(bg="green")
    norm_off_button.config(bg=root.cget("bg"))
    norm = 1
    print("Normalize On")
    select_BBDS(0)


def norm_off():
    global norm
    norm_off_button.config(bg="green")
    norm_on_button.config(bg=root.cget("bg"))
    norm = 0
    print("Normalize Off")
    select_BBDS(0)


# Function to handle file selection
def select_MTS(prompt):
    global mtsnp, file_path_mts
    if prompt == 1:
        file_path_mts = filedialog.askopenfilename(
            filetypes=[
                ("TXT File", "*.TXT"),
                ("txt File", "*.txt"),
                ("CSV File", "*.csv"),
                ("Data File", "*.dat"),
            ]
        )

    file1_path = file_path_mts
    mts = pd.read_csv(
        file1_path, sep="\t", header=None, skiprows=8, names=["Displ", "Force", "Time"]
    )
    mts["Time"] = mts["Time"].astype(int)
    mts.drop(mts[mts.Time < dwell_time.get()].index, inplace=True)  # added
    mts = mts.drop_duplicates(subset=["Time"], ignore_index=True)
    mts2 = pd.DataFrame(columns=["Time", "Stress", "Strain"])
    mts2["Stress"] = mts["Force"].apply(
        lambda x: (x / (thickness.get() * width.get())) * 1000
    )
    mts2["Strain"] = mts["Displ"].apply(lambda x: (x / gage_length.get()))
    mts2["Time"] = mts["Time"]
    mts2.drop(mts2[mts2.Time % interval_time.get() != 0].index, inplace=True)
    mtsnp = mts2.to_numpy()
    button1.config(bg="green")
    print("MTS Data loaded from: " + Path(file_path_mts).name)
    # return mtsnp


def select_BBDS(prompt):
    global bbdsnp, file_path_bbds, norm

    if prompt == 1:
        norm = 0
        norm_off_button.config(bg="green")
        norm_on_button.config(bg=root.cget("bg"))
        file_path_bbds = filedialog.askopenfilename(
            filetypes=[
                ("TXT File", "*.TXT"),
                ("txt File", "*.txt"),
                ("CSV File", "*.csv"),
                ("Data File", "*.dat"),
            ]
        )

    file2_path = file_path_bbds
    bbds = pd.read_csv(
        file2_path,
        sep="\t",
        header=None,
        skiprows=3,
        names=["Time", "Real", "Imag", "Zp_real", "Zp_imag"],
    )
    # bbds.drop(bbds[bbds.Time < 30].index, inplace=False)  # added
    bbds = bbds[bbds["Time"] >= dwell_time.get()].reset_index(drop=True)

    # normalize variables
    if norm == 1:

        bbds["Real"] = bbds["Real"].apply(lambda x: x / bbds.loc[0, "Real"])
        bbds["Imag"] = bbds["Imag"].apply(lambda x: x / bbds.loc[0, "Imag"])


        bbds["Zp_real"] = bbds["Zp_real"].apply(lambda x: x / bbds.loc[0, "Zp_real"])
        bbds["Zp_imag"] = bbds["Zp_imag"].apply(lambda x: x / bbds.loc[0, "Zp_imag"])

    bbdsnp = bbds.to_numpy()
    button2.config(bg="green")
    print("BBDS Data loaded from: " + Path(file_path_bbds).name)
    # return bbdsnp
    # return bbds


# Function to plot the data
def plot_data(plot_selection):
    # Read data from the files using pandas
    global canvas, finaldf

    plt.cla()
    # BBDS Data Cleaning
    finaldf = pd.DataFrame(
        columns=["Strain", "Stress", "Real", "Imag", "Zp_Real", "Zp_Imag", "TanD"]
    )

    finaldf["Real"] = pd.Series(bbdsnp[:, 1])
    finaldf["Imag"] = pd.Series(bbdsnp[:, 2])
    finaldf["TanD"] = ((pd.Series(bbdsnp[:, 2])/pd.Series(bbdsnp[:, 1]))*180/3.1416)-90

    finaldf["Zp_Real"] = pd.Series(bbdsnp[:, 3])
    finaldf["Zp_Imag"] = pd.Series(bbdsnp[:, 4])

    finaldf["Stress"] = pd.Series(mtsnp[:, 1])
    finaldf["Strain"] = pd.Series(mtsnp[:, 2])
    finaldf = finaldf.drop_duplicates(subset=["Strain"], ignore_index=True)
    finaldf.drop(finaldf[finaldf.Real <= 0].index, inplace=True)
    # Clear previous plot
    plt.clf()

    # Plot the data
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    finaldf.plot(
        kind="line", x="Strain", y="Stress", ax=ax1, label="Stress", legend=False
    )
    ax1.legend(loc="upper left")
    if plot_selection == 0:

        finaldf.plot(
            kind="line",
            x="Strain",
            y="Real",
            color="r",
            ax=ax2,
            label="Real Perm.",
            legend=False,
        )
        ax2.set_ylabel("Real Perm.", fontsize=14, fontfamily='Arial', fontweight='bold')
    elif plot_selection == 2:

        finaldf.plot(
            kind="line",
            x="Strain",
            y="Zp_Real",
            color="r",
            ax=ax2,
            label="Real Imp.",
            legend=False,
        )
        ax2.set_ylabel("Zp' [Ohm]", fontsize=14, fontfamily='Arial', fontweight='bold')
    elif plot_selection == 3:

        finaldf.plot(
            kind="line",
            x="Strain",
            y="Zp_Imag",
            color="r",
            ax=ax2,
            label="Imag Imp.",
            legend=False,
        )
        ax2.set_ylabel("Zp'' [Ohm]", fontsize=14, fontfamily='Arial', fontweight='bold')
    elif plot_selection == 1:

        finaldf.plot(
            kind="line",
            x="Strain",
            y="Imag",
            color="r",
            ax=ax2,
            label="Imag Perm.",
            legend=False,
        )
        ax2.set_ylabel("Imag Perm.", fontsize=14, fontfamily='Arial', fontweight='bold')

    elif plot_selection == 4:

        finaldf.plot(
            kind="line",
            x="Strain",
            y="TanD",
            color="r",
            ax=ax2,
            label="Tan Delta",
            legend=False,
        )
        ax2.set_ylabel("Tan Delta", fontsize=14, fontfamily='Arial', fontweight='bold')

    ax1.set_ylabel("Stress (MPa)", fontsize=14, fontfamily='Arial', fontweight='bold')

    ax1.set_xlabel("Strain", fontsize=14, fontfamily='Arial', fontweight='bold')

    ax2.legend(loc="lower right")

    # Embed the plot in the Tkinter window
    canvas = FigureCanvasTkAgg(plt.gcf(), master=root)
    canvas.draw()
    canvas.get_tk_widget().grid(row=15, column=0, columnspan=80)
    buttons[0].configure(bg=root.cget("bg"))
    buttons[1].configure(bg=root.cget("bg"))
    buttons[2].configure(bg=root.cget("bg"))
    buttons[3].configure(bg=root.cget("bg"))
    buttons[plot_selection].configure(bg="green")
    print("Data plotted for" + str ((df.iloc[0, plot_selection+1])))


def close_plot():
    global canvas, bbdsnp, mtsnp, finaldf
    bbdsnp = []
    mtsnp = []
    finaldf = pd.DataFrame()
    plt.cla()
    plt.clf()
    # for item in canvas.get_tk_widget().find_all():
    #     canvas.get_tk_widget().delete(item)
    canvas.get_tk_widget().destroy()
    button1.config(bg=root.cget("bg"))
    button2.config(bg=root.cget("bg"))
    print("Data reset! Start again!")


def save_file():
    filepath = filedialog.asksaveasfilename(
        defaultextension=".dat",
        filetypes=[
            ("Data File", "*.dat"),
            ("txt File", "*.txt"),
            ("CSV File", "*.csv"),
        ],
    )
    finaldf.to_csv(filepath, sep="\t", index=False)
    print("File saved to: " + Path(filepath).name)


def save_plot():
    filepath = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("JPG File", "*.jpg"), ("PNG File", "*.png"), ("EPS File", "*.eps")],
    )
    plt.savefig(filepath, dpi=300)
    print("image saved to: " + Path(filepath).name)

def confirm_butt():
    select_MTS(0)
    print("Confirmed Geometry and Time Parameters: ")
    print("Thickness (mm): " + str(thickness.get()))
    print("Gage Length (mm): " + str(gage_length.get()))
    print("Width (mm): " + str(width.get()))
    print("BBDS Interval (s): " + str(interval_time.get()))


# Create a console window
console_window = tk.Text(root, height=3, width=80)
console_window.grid(row=0, column=0, columnspan=30)
console_window.insert(
    tk.END, "Welcome to BBDS-MTS GUI v2024! Confirm constants, Load data and Plot!\n"
)


# Create input boxes for thickness, gage length, width, and interval time
thickness_label = tk.Label(root, text="Thickness (mm)")
thickness_label.grid(row=2, column=0, columnspan=1)
thickness_entry = tk.Entry(root, textvariable=thickness)
thickness_entry.grid(row=3, column=0, columnspan=1)

gage_length_label = tk.Label(root, text="Gage Length (mm)")
gage_length_label.grid(row=4, column=0, columnspan=1)
gage_length_entry = tk.Entry(root, textvariable=gage_length)
gage_length_entry.grid(row=5, column=0, columnspan=1)

width_label = tk.Label(root, text="Width (mm)")
width_label.grid(row=6, column=0, columnspan=1)
width_entry = tk.Entry(root, textvariable=width)
width_entry.grid(row=7, column=0, columnspan=1)

interval_time_label = tk.Label(root, text="Interval Time (s)")
interval_time_label.grid(row=8, column=0, columnspan=1)
interval_time_entry = tk.Entry(root, textvariable=interval_time)
interval_time_entry.grid(row=9, column=0, columnspan=1)

dwell_label = tk.Label(root, text="Dwell Time (s)")
dwell_label.grid(row=10, column=0, columnspan=1)
dwell_entry = tk.Entry(root, textvariable=dwell_time)
dwell_entry.grid(row=11, column=0, columnspan=1)

confirm_button = tk.Button(
    root, text="Confirm", command=lambda: confirm_butt(), font="Helvetica 10 bold"
)
confirm_button.grid(row=14, column=0, columnspan=1)

# Create the buttons for file selection
button1 = tk.Button(
    root, text="MTS File", command=lambda: select_MTS(1), font="Helvetica 10 bold"
)
button1.grid(row=12, column=0, columnspan=1)

button2 = tk.Button(
    root, text="BBDS File", command=lambda: select_BBDS(1), font="Helvetica 10 bold"
)
button2.grid(row=13, column=0, columnspan=1)

# Create the plot button

Click_Plot_label = tk.Label(root, text="Click to Plot!")
Click_Plot_label.grid(row=3, column=7, columnspan=5)

fig, ax1 = plt.subplots()
ax2 = ax1.twinx()

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().grid(row=15, column=0, columnspan=30)

buttons = []
for i in range(5):
    button_text = "TanD" if i == 4 else df.iloc[0, i + 1].strip()
    button = tk.Button(
        root,
        text=button_text,
        command=lambda i=i: plot_data(i),
        activebackground="#00ff00",
        font="Helvetica 10 bold",
        justify="center",
    )
    # k=i+4
    button.grid(row=5 + i, column=7, columnspan=5)  # , columnspan=15)
    buttons.append(button)

# Create the close plot button
close_button = tk.Button(
    root, text="Reset", command=close_plot, font="Helvetica 10 bold"
)
close_button.grid(row=7, column=17, columnspan=5)

# save button
save_txt_button = tk.Button(
    root,
    text="Save Data",
    command=save_file,
    activebackground="#00ff00",
    bd=3,
    font="Helvetica 10 bold",
)
save_txt_button.grid(row=5, column=17, columnspan=5)
save_button = tk.Button(
    root,
    text="Save Plot",
    command=save_plot,
    activebackground="#00ff00",
    bd=3,
    font="Helvetica 10 bold",
)
save_button.grid(row=6, column=17, columnspan=5)

norm_on_button = tk.Button(
    root,
    text="Normalize on",
    command=norm_on,
    activebackground="#00ff00",
    bd=3,
    font="Helvetica 10 bold",
    justify="center",
)
norm_on_button.grid(row=12, column=7, columnspan=8)
norm_off_button = tk.Button(
    root,
    text="Normalize off",
    command=norm_off,
    activebackground="#00ff00",
    bd=3,
    font="Helvetica 10 bold",
    justify="center",
)
norm_off_button.grid(row=13, column=7, columnspan=8)


# Redirect sys.stdout to the console window
sys.stdout = ConsoleRedirector(console_window)

# Run the Tkinter event loop
root.mainloop()
