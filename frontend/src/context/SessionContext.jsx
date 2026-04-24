import React, { createContext, useState } from 'react';

export const SessionContext = createContext(null);

const safeParse = (key, fallback) => {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
};

export const SessionProvider = ({ children }) => {
  const [userProfile, setUserProfileState] = useState(
    () => safeParse('aarogyaaid_profile', null)
  );
  const [recommendationResult, setRecommendationResultState] = useState(
    () => safeParse('aarogyaaid_result', null)
  );
  const [conversationHistory, setConversationHistoryState] = useState(
    () => safeParse('aarogyaaid_chat_history', [])
  );
  const [authToken, setAuthTokenState] = useState(
    () => localStorage.getItem('aarogyaaid_token') || null
  );
  const [currentUser, setCurrentUser] = useState(
    () => safeParse('aarogyaaid_user', null)
  );

  const setAuthToken = (token, user) => {
    setAuthTokenState(token);
    setCurrentUser(user);
    if (token) {
      localStorage.setItem('aarogyaaid_token', token);
      localStorage.setItem('aarogyaaid_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('aarogyaaid_token');
      localStorage.removeItem('aarogyaaid_user');
      localStorage.removeItem('aarogyaaid_profile');
      localStorage.removeItem('aarogyaaid_result');
      localStorage.removeItem('aarogyaaid_chat_history');
      setUserProfileState(null);
      setRecommendationResultState(null);
      setConversationHistoryState([]);
    }
  };

  const setUserProfile = (profile) => {
    setUserProfileState(profile);
    if (profile) localStorage.setItem('aarogyaaid_profile', JSON.stringify(profile));
    else localStorage.removeItem('aarogyaaid_profile');
  };

  const setRecommendationResult = (result) => {
    setRecommendationResultState(result);
    if (result) localStorage.setItem('aarogyaaid_result', JSON.stringify(result));
    else localStorage.removeItem('aarogyaaid_result');
  };

  const setConversationHistory = (history) => {
    setConversationHistoryState(history);
    // ChatPanel also writes to localStorage directly for performance;
    // this keeps context in sync.
  };

  return (
    <SessionContext.Provider value={{
      userProfile, setUserProfile,
      recommendationResult, setRecommendationResult,
      conversationHistory, setConversationHistory,
      authToken, currentUser, setAuthToken,
    }}>
      {children}
    </SessionContext.Provider>
  );
};