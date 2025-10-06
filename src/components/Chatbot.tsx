import { useState, useEffect, useRef } from 'react';
import { Send, Bot, User as UserIcon } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { storage } from '../utils/storage';
import { ChatMessage } from '../types';
import { generateChatResponse } from '../utils/aiCoach';

export default function Chatbot() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadMessages();
  }, [user]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadMessages = () => {
    const allMessages = storage.getMessages().filter(m => m.userId === user?.id);
    setMessages(allMessages);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || !user) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setIsTyping(true);

    const expenses = storage.getExpenses().filter(e => e.userId === user.id);
    const categories = storage.getCategories();
    const goals = storage.getGoals().filter(g => g.userId === user.id);
    const activeGoal = goals.find(g => g.active) || null;

    setTimeout(() => {
      const aiResponse = generateChatResponse(userMessage, expenses, categories, activeGoal);

      const newMessage: ChatMessage = {
        id: `msg-${Date.now()}`,
        userId: user.id,
        message: userMessage,
        response: aiResponse,
        createdAt: new Date().toISOString(),
      };

      const allMessages = storage.getMessages();
      allMessages.push(newMessage);
      storage.setMessages(allMessages);

      setMessages(prev => [...prev, newMessage]);
      setIsTyping(false);
    }, 1000);
  };

  const suggestedQuestions = [
    "What's my biggest expense this month?",
    "How can I save on transport?",
    "Am I close to my goal?",
    "Give me savings tips",
  ];

  return (
    <div className="space-y-6 h-full">
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl p-6 text-white">
        <div className="flex items-center gap-3 mb-2">
          <div className="bg-white rounded-full p-2">
            <Bot className="w-6 h-6 text-blue-600" />
          </div>
          <h2 className="text-2xl font-bold">AI Financial Coach</h2>
        </div>
        <p className="text-blue-100">Ask me anything about your finances and get personalized advice!</p>
      </div>

      <div className="bg-white rounded-lg shadow-md flex flex-col" style={{ height: 'calc(100vh - 300px)' }}>
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center py-12">
              <div className="bg-blue-100 rounded-full p-4 w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                <Bot className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">
                Welcome! I'm your AI Financial Coach
              </h3>
              <p className="text-gray-600 mb-6">
                Ask me questions about your spending, savings, or financial goals.
              </p>
              <div className="space-y-2 max-w-md mx-auto">
                <p className="text-sm font-medium text-gray-700 mb-3">Try asking:</p>
                {suggestedQuestions.map((question, idx) => (
                  <button
                    key={idx}
                    onClick={() => setInputMessage(question)}
                    className="block w-full text-left px-4 py-3 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors text-sm"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <div key={msg.id} className="space-y-3">
                  <div className="flex items-start gap-3 justify-end">
                    <div className="bg-blue-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 max-w-[80%]">
                      <p className="text-sm">{msg.message}</p>
                    </div>
                    <div className="bg-blue-600 rounded-full p-2 flex-shrink-0">
                      <UserIcon className="w-5 h-5 text-white" />
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="bg-blue-100 rounded-full p-2 flex-shrink-0">
                      <Bot className="w-5 h-5 text-blue-600" />
                    </div>
                    <div className="bg-gray-100 text-gray-800 rounded-2xl rounded-tl-sm px-4 py-3 max-w-[80%]">
                      <p className="text-sm">{msg.response}</p>
                    </div>
                  </div>
                </div>
              ))}

              {isTyping && (
                <div className="flex items-start gap-3">
                  <div className="bg-blue-100 rounded-full p-2 flex-shrink-0">
                    <Bot className="w-5 h-5 text-blue-600" />
                  </div>
                  <div className="bg-gray-100 text-gray-800 rounded-2xl rounded-tl-sm px-4 py-3">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        <div className="border-t border-gray-200 p-4">
          <form onSubmit={handleSubmit} className="flex gap-3">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Ask about your finances..."
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
              disabled={isTyping}
            />
            <button
              type="submit"
              disabled={isTyping || !inputMessage.trim()}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
