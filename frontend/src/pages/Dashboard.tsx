import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router';
import { type Course } from '../utils/Course.ts';
import { TermCard } from '../components/TermCard.tsx';
import { useAuthContext } from '../context/AuthContext.tsx'

interface GradesData {
  [termCode: string]: Course[];
}

export function Dashboard(){
  const [searching, setSearching] = useState('');
  const [grades, setGrades] = useState<GradesData | null>(null);
  const {token, setToken} = useAuthContext();
  const [cumulativeGpa, setCumulativeGpa] = useState(0);
  const [totalCredits, setTotalCredits] = useState(0);
  const [termsCount, setTermsCount] = useState(0);
  const [lastUpdated, setLastUpdated] = useState('');

  const navigate = useNavigate();

  function info(){
    if (!grades) return;
    let totalQP: number = 0;
    let totalGH: number = 0;
    let totalEarned: number = 0;
    let cumulativegpa: number = 0;
    let totalcredits: number = 0;
    let termscount: number = 0;
    Object.entries(grades).forEach(([_, courses]) => courses.forEach(course => {
      totalQP += Number(course.qualitypoints);
      totalGH += Number(course.gpahours);
      totalEarned += Number(course.earned);
    }))
    
    cumulativegpa = totalQP/totalGH;
    totalcredits = totalEarned;
    termscount = Object.keys(grades).length;
    setCumulativeGpa(cumulativegpa);
    setTotalCredits(totalcredits);
    setTermsCount(termscount);
  }

  async function handleRefresh(){
    const _ = await fetch(`${import.meta.env.VITE_API_URL}/grades/check`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      }
    });
    const response = await fetch(`${import.meta.env.VITE_API_URL}/grades`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      }
    });
    const data = await response.json();
    setGrades(data.grades);
    setLastUpdated(data.last_updated);
  }

  function redirectToProfile(){
    navigate("/app/profile");
  }

  function logOut(){
    localStorage.removeItem('token');
    setToken('');
    navigate("/login");
  }

  useEffect(() => {
    async function fetchGrades(){
      const response = await fetch(`${import.meta.env.VITE_API_URL}/grades`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        }
      });
      const data = await response.json();
      setGrades(data.grades);
      setLastUpdated(data.last_updated);
    }
    fetchGrades();
  }, [])

  useEffect(() => {
    info();
  }, [grades])

  return (
    <div className="dashboard-component">
      <div className="header">
        <h1 className="title">Cu Scraper</h1>
        <button className="refresh-btn" onClick={handleRefresh}>Refresh Grades</button>
        <button className="profile-btn" onClick={redirectToProfile}></button>
        <button className="logout-btn" onClick={logOut}></button>
      </div>
      <div className="info-component">
        <label className="cumulativegpa-label">Cumulative GPA</label>
        <label className="totalcredits-label">Total Credits</label>
        <label className="terms-label">Terms</label>
        <label className="lastupdated-label">Last updated</label>
        <p className="cumulativegpa">{cumulativeGpa}</p>
        <p className="totalcredits">{totalCredits}</p>
        <p className="terms">{termsCount}</p>
        <p className="lastupdated">{new Date(lastUpdated).toLocaleString()}</p>
      </div>
      <div className="search-bar"> 
        <input className="search" placeholder="Search courses..." onChange={v => setSearching(v.target.value)}/> 
      </div>
      <div className="terms-table">
        {grades ? Object.entries(grades).map(([termCode, courses]) => 
          <TermCard key={termCode} termCode={termCode} courses={courses.filter(course => course.coursetitle.toLowerCase().includes(searching.toLowerCase()))}/>
        ) : ''}
      </div>
    </div>
  ) 
}
