// Firebase配置初始化文件
// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyBJQEoasQOFFeE4vvT_T2vgk6MFo2LZZ9o",
  authDomain: "namecard-ocr-system.firebaseapp.com",
  projectId: "namecard-ocr-system",
  storageBucket: "namecard-ocr-system.firebasestorage.app",
  messagingSenderId: "615261462909",
  appId: "1:615261462909:web:dc900109a8fb629b8fac14",
  measurementId: "G-X7SDJM3NVP"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app); 