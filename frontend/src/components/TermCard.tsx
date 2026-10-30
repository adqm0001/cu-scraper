import { type Course } from '../utils/Course.ts';
import './TermCard.css';

interface TermProps {
  termCode: string;
  courses: Course[];
  allCourses: Course[];
}

export function TermCard({ termCode, courses, allCourses }: TermProps) {
  function calcTermGpa(): number | null {
    let totalQP = 0;
    let totalGH = 0;
    allCourses.forEach(c => {
      totalQP += Number(c.qualitypoints);
      totalGH += Number(c.gpahours);
    });
    return totalGH > 0 ? totalQP / totalGH : null;
  }

  const gpa = calcTermGpa();
  const seasons: Record<string, string> = { '10': 'Winter', '20': 'Summer', '30': 'Fall' };
  const season = seasons[termCode.slice(4)];
  const termName = season ? `${season} ${termCode.slice(0, 4)}` : termCode;

  return (
    <div className="term-card">
      <div className="term-header">
        <div className="term-heading"><h3 className="term-name">{termName}</h3><span className="term-course-count">{allCourses.length} courses</span></div>
        {gpa !== null && (
          <span className="term-gpa-badge">Term GPA <strong>{gpa.toFixed(2)}</strong></span>
        )}
      </div>

      {courses.length === 0 ? (
        <p className="no-courses">No courses this term.</p>
      ) : (
        <div className="table-scroll">
          <table className="course-table">
            <thead>
              <tr>
                <th>Course</th>
                <th>Title</th>
                <th>Grade</th>
                <th>Credits</th>
                <th>Quality Points</th>
              </tr>
            </thead>
            <tbody>
              {courses.map(course => (
                <tr key={course.crn}>
                  <td className="td-code">{course.subject} {course.course}</td>
                  <td className="td-title">{course.coursetitle}</td>
                  <td className="td-grade">{course.finalgrade || '—'}</td>
                  <td className="td-credits">{course.attempted}</td>
                  <td className="td-qp">{course.qualitypoints || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
