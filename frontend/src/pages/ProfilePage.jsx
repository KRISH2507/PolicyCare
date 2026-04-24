import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { SessionContext } from '../context/SessionContext';
import { apiPost } from '../api/client';
import styles from '../styles/ProfilePage.module.css';

const ProfilePage = () => {
  const [formData, setFormData] = useState({
    full_name: '', age: '', city_tier: 'metro', lifestyle: 'sedentary',
    pre_existing_conditions: [], income_band: 'under3l'
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [submitError, setSubmitError] = useState(null);

  const { setUserProfile, setRecommendationResult } = useContext(SessionContext);
  const navigate = useNavigate();

  const conditionsMap = ['diabetes', 'hypertension', 'asthma', 'cardiac', 'none', 'other'];
  const conditionsLabels = ['Diabetes', 'Hypertension', 'Asthma', 'Cardiac condition', 'None', 'Other'];

  const toggleCondition = (val) => {
    setFormData(prev => {
      let arr = [...prev.pre_existing_conditions];
      if (val === 'none') return { ...prev, pre_existing_conditions: ['none'] };
      
      const idx = arr.indexOf('none');
      if (idx > -1) arr.splice(idx, 1);
      
      if (arr.includes(val)) arr = arr.filter(c => c !== val);
      else arr.push(val);
      
      return { ...prev, pre_existing_conditions: arr };
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrors({});
    setSubmitError(null);
    
    let hasErr = false;
    let newErrs = {};
    if (!formData.full_name.trim()) { newErrs.full_name = 'Full name is required'; hasErr = true; }
    const ageNum = parseInt(formData.age, 10);
    if (!formData.age || isNaN(ageNum) || ageNum < 1 || ageNum > 99) { newErrs.age = 'Enter a valid age (1–99)'; hasErr = true; }
    if (hasErr) return setErrors(newErrs);

    setLoading(true);
    try {
      const response = await apiPost('/api/recommend/', formData);
      setUserProfile(formData);
      setRecommendationResult(response);
      navigate('/results');
    } catch (err) {
      setSubmitError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>Find your health plan</h2>
      <p className={styles.subtitle}>Your answers help us find a plan that actually fits your life.</p>
      
      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.field}>
          <label>Full name</label>
          <input type="text" placeholder="Enter your full name" value={formData.full_name} onChange={e => setFormData({...formData, full_name: e.target.value})} disabled={loading} />
          {errors.full_name && <span className={styles.errorText}>{errors.full_name}</span>}
        </div>
        
        <div className={styles.field}>
          <label>Age</label>
          <input type="number" min="1" max="99" placeholder="Your age in years" value={formData.age} onChange={e => setFormData({...formData, age: e.target.value})} disabled={loading} />
          {errors.age && <span className={styles.errorText}>{errors.age}</span>}
        </div>

        <div className={styles.field}>
          <label>Where do you live?</label>
          <select value={formData.city_tier} onChange={e => setFormData({...formData, city_tier: e.target.value})} disabled={loading}>
            <option value="metro">Metro city</option>
            <option value="tier2">Tier-2 city</option>
            <option value="tier3">Tier-3 city / town</option>
          </select>
        </div>

        <div className={styles.field}>
          <label>How would you describe your lifestyle?</label>
          <select value={formData.lifestyle} onChange={e => setFormData({...formData, lifestyle: e.target.value})} disabled={loading}>
            <option value="sedentary">Sedentary (desk job, low activity)</option>
            <option value="moderate">Moderate (some exercise weekly)</option>
            <option value="active">Active (regular exercise)</option>
            <option value="athlete">Athlete (intense daily activity)</option>
          </select>
        </div>

        <div className={styles.field}>
          <label>Do you have any pre-existing conditions?</label>
          <div className={styles.sublabel}>Select all that apply</div>
          <div className={styles.checkboxGrid}>
            {conditionsMap.map((val, i) => (
              <label key={val} className={styles.checkboxWrapper}>
                <input type="checkbox" checked={formData.pre_existing_conditions.includes(val)} onChange={() => toggleCondition(val)} disabled={loading} />
                {conditionsLabels[i]}
              </label>
            ))}
          </div>
        </div>

        <div className={styles.field}>
          <label>What is your approximate annual income?</label>
          <select value={formData.income_band} onChange={e => setFormData({...formData, income_band: e.target.value})} disabled={loading}>
            <option value="under3l">Under ₹3 lakh</option>
            <option value="3to8l">₹3–8 lakh</option>
            <option value="8to15l">₹8–15 lakh</option>
            <option value="above15l">Above ₹15 lakh</option>
          </select>
        </div>

        <button type="submit" disabled={loading} className={styles.submitBtn}>
          {loading ? 'Finding your plan…' : 'Find my plan →'}
        </button>
        {submitError && <div className={styles.errorText} style={{textAlign: 'center', marginTop: '12px'}}>{submitError}</div>}
      </form>
    </div>
  );
};

export default ProfilePage;