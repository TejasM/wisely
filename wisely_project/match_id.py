__author__ = 'tmehta'
from pandas import read_csv, Series
from users.models import Course
import numpy as np

f = read_csv('CourseSkills-edXCourses.csv')

courses = f['Course Name']
f['Course Id'] = Series(np.random.randn(f.shape[0]), index=f.index)

for i, c in enumerate(courses):
    if isinstance(c, str):
        c = c.strip()
        django_course = Course.objects.filter(title__contains=c)
        if django_course.count() != 0:
            f['Course Id'][i] = django_course[0].course_id

f.to_csv('CourseSkills-edXCourses.csv')