__author__ = 'tmehta'
from pandas import read_csv

f = read_csv('CourseSkills-edXCourses.csv')

courses = f['Course Name']

for c in courses:
    c = c.strip()