import { type Course } from '../utils/Course.ts';
import './TermCard.css';

interface TermProps {
  termCode: string;
  courses: Course[];
}

export function TermCard({ termCode, courses }: TermProps) {
  function calcTermGpa(): number | null {
    let totalQP = 0;
    let totalGH = 0;
    courses.forEach(c => {
      totalQP += Number(c.qualitypoints);
      totalGH += Number(c.gpahours);
    });
    return totalGH > 0 ? totalQP / totalGH : null;
  }

  const gpa = calcTermGpa();

  return (
    <div className="term-card">
      <div className="term-header">
        <span className="term-name">{termCode}</span>
        {gpa !== null && (
          <span className="term-gpa-badge">GPA {gpa.toFixed(2)}</span>
        )}
      </div>

      {courses.length === 0 ? (
        <p className="no-courses">No courses this term.</p>
      ) : (
        <table className="course-table">
          <thead>
            <tr>
              <th>Course</th>
              <th>Title</th>
              <th>Grade</th>
              <th>Credits</th>
            </tr>
          </thead>
          <tbody>
            {courses.map(course => (
              <tr key={course.crn}>
                <td className="td-code">{course.subject} {course.course}</td>
                <td className="td-title">{course.coursetitle}</td>
                <td className="td-grade">{course.finalgrade || '—'}</td>
                <td className="td-credits">{course.attempted}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
