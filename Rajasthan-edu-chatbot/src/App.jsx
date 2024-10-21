import { useState } from 'react'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import './App.css'
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import Contact from './components/Contact';
import About from './components/About';
import GetStarted from './components/GetStarted';
import Home from './components/Home';

function App() {

  const router = createBrowserRouter([
    {
      path: '/contact',
      element: <>
        <Navbar /> <Contact />
      </>
    },
    {
      path: '/about',
      element: <>
        <Navbar /> <About />
      </>
    },
    {
      path: '/getstarted',
      element: <>
        <Navbar /> <GetStarted />
      </>
    },
    {
      path: '/home',
      element: <>
        <Navbar /> <Home />
      </>
    }
  ]);

  return (
    <>


      <div className="relative h-full w-full bg-slate-950"><div className="absolute bottom-0 left-0 right-0 top-0 bg-[linear-gradient(to_right,#4f4f4f2e_1px,transparent_1px),linear-gradient(to_bottom,#4f4f4f2e_1px,transparent_1px)] bg-[size:14px_24px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]"></div>
        <div className="min-h-[99vh]">
          <RouterProvider router={router} />
        </div>
      </div>
      <Footer />
    </>
  )
}

export default App
