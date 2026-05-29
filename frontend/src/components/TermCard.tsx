import { type Course } from '../utils/Course.ts';

interface TermProps {
  termCode: string;
  courses: Course[];
}

export function TermCard({termCode, courses}: TermProps){
  function calculatetermgpa(): number{
    let totalQP: number = 0;
    let totalGH: number = 0;
    courses.forEach((course) => {
      totalQP += Number(course.qualitypoints);
      totalGH += Number(course.gpahours);
    });
    return totalQP/totalGH;
  }

  return (
    <div className="term-component">
      <div className="header">
        <h1 className="term-code">{termCode}</h1>
        <h2 className="term-gpa">{calculatetermgpa()}</h2>
      </div>
      <div className="courses-categories">
        <label className="course-label">Course</label>
        <label className="title-label">Title</label>
        <label className="grade-label">Grade</label>
        <label className="credits-label">Creditd</label>
      </div>
      <div className="courses-table">
        {courses.map((course) =>
          <div key={course.crn}>
          <h2 className="course">{course.subject}</h2>
          <p className="title">{course.coursetitle}</p>
          <p className="grade">{course.finalgrade}</p>
          <p className="attempted">{course.attempted}</p>
          </div>
        )}
      </div>
    </div>
  ) 
}
