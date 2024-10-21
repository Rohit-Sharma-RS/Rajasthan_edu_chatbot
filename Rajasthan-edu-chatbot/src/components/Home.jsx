import React, { useState, useRef, useEffect } from 'react';

const Home = () => {
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const chatEndRef = useRef(null);

    const handleSendMessage = (e) => {
        e.preventDefault();
        if (inputValue.trim() === '') return;

        const newMessage = { text: inputValue, sender: 'user' };
        setMessages([...messages, newMessage]);
        setInputValue(''); // Reset input field

        // Simulate bot response
        setTimeout(() => {
            const botMessage = { text: 'This is an automatic response from EduBot.', sender: 'bot' };
            setMessages((prevMessages) => [...prevMessages, botMessage]);
        }, 1000);
    };

    // Auto-scroll to bottom when a new message is added
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <div className="min-h-screen w-full flex flex-col items-center justify-center bg-gray-900 text-white p-4">
            <h1 className='text-4xl mb-6 font-semibold'>Your Rajasthan Education Companion</h1>

            <div className="flex flex-col justify-between w-fit md:m-10 md:w-auto h-auto bg-gray-800 rounded-xl shadow-xl">
                {/* Chat Messages */}
                <div className=" flex-grow overflow-y-auto p-4 bg-gray-700 rounded-t-lg scrollbar-hide z-30">
                    <div className="flex flex-col space-y-4 ">
                        {messages.map((message, index) => (
                            <div key={index} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                                <div className={`p-4  rounded-lg ${message.sender === 'user' ? 'bg-blue-500' : 'bg-gray-500'} max-w-xs text-white break-words`}>
                                    {message.text}
                                </div>
                            </div>
                        ))}
                        <div ref={chatEndRef} />
                    </div>
                </div>
                {/* Chat Input */}
                <form onSubmit={handleSendMessage} className="p-4 bg-gray-600 rounded-b-lg flex items-center space-x-4">
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder="Type your message..."
                        className="z-10 w-[60vw] h-14 pl-4 pr-20 rounded-full bg-gray-600 text-white focus:outline-none border border-gray-500"
                    />

                    <button
                        type="submit"
                        className="bg-blue-600 hover:bg-blue-700 focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-full px-6 py-2 transition-all duration-300 transform hover:scale-105"
                    >
                        Send
                    </button>
                </form>
            </div>
        </div>
    );
};

export default Home;
