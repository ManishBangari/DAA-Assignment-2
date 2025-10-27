import openpyxl
from openpyxl import Workbook
import streamlit as st
import pandas as pd
import math, csv, os, glob, re, base64
from io import BytesIO

# Opening the worksheet
df = pd.read_csv('Data/input_btp_mtp_allocation.csv')

#print(df.head())
total_students = df.shape[0]-1
total_faculty = df.shape[1]-4

#print(total_faculty, total_students)

# Sorting the CGPA in descending order
# Sort in ascending order (lowest to highest CGPA)
df_sorted = df.sort_values(by="CGPA")

# OR sort in descending order (highest to lowest CGPA)
df_sorted = df.sort_values(by="CGPA", ascending=False)

df_sorted.to_csv("students_sorted.csv", index=False)

print(df_sorted.head())
print(df.head())