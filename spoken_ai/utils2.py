class TextAnalysisPipeline:
    def __init__(self, api_key="sk-feb07e3e5a804d64a7ffdd0305527377", base_url="https://api.deepseek.com/v1", log_file="session_log.jsonl"):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.log_file = log_file
        self.session_histories = {}  # session_id -> 对话历史
        self.max_history_turns = 5   # 每个会话最大对话轮数
        self.session_timeout = 3600  # 会话超时时间（1小时）
        
        if not os.path.exists(self.log_file):
            open(self.log_file, "w", encoding="utf-8").close()

    def short_response(self, transcribed_text, session_id="default"):
        """
        基于session ID的带上下文回应
        """
        # 清理过期会话
        self._cleanup_expired_sessions()
        
        # 获取或创建会话历史
        if session_id not in self.session_histories:
            self.session_histories[session_id] = {
                'history': [],
                'last_activity': datetime.datetime.now()
            }
        
        session_data = self.session_histories[session_id]
        conversation_history = session_data['history']
        session_data['last_activity'] = datetime.datetime.now()  # 更新活动时间
        
        # 构建消息
        system_prompt = """You are a friendly English speaking partner. 
        Reply briefly and naturally as if in a real conversation. 
        Keep your response within 1-2 sentences. 
        Maintain context from our previous exchanges and respond appropriately."""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # 添加历史对话（最近几轮）
        for msg in conversation_history[-self.max_history_turns*2:]:
            messages.append(msg)
        
        # 添加当前用户输入
        messages.append({"role": "user", "content": transcribed_text})
        
        # 调用API
        rsp = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.7,
            stream=False
        )
        
        assistant_reply = rsp.choices[0].message.content.strip()
        print(f"[SESSION {session_id}] Assistant: {assistant_reply}")
        
        # 更新会话历史
        self._update_session_history(
            session_id,
            {"role": "user", "content": transcribed_text},
            {"role": "assistant", "content": assistant_reply}
        )
        
        return assistant_reply

    def _update_session_history(self, session_id, user_message, assistant_message):
        """更新特定会话的历史"""
        if session_id not in self.session_histories:
            return
            
        history = self.session_histories[session_id]['history']
        history.append(user_message)
        history.append(assistant_message)
        
        # 控制历史长度，保留最近的对话
        max_messages = self.max_history_turns * 2
        if len(history) > max_messages:
            self.session_histories[session_id]['history'] = history[-max_messages:]

    def _cleanup_expired_sessions(self):
        """清理过期会话以释放内存"""
        current_time = datetime.datetime.now()
        expired_sessions = []
        
        for session_id, session_data in self.session_histories.items():
            time_diff = (current_time - session_data['last_activity']).total_seconds()
            if time_diff > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.session_histories[session_id]
            print(f"[SESSION] Cleaned up expired session: {session_id}")

    def get_session_history(self, session_id="default"):
        """获取特定会话的历史记录（用于调试或显示）"""
        if session_id in self.session_histories:
            return self.session_histories[session_id]['history']
        return []

    def clear_session_history(self, session_id="default"):
        """清空特定会话历史"""
        if session_id in self.session_histories:
            self.session_histories[session_id]['history'] = []
            return True
        return False

    def get_active_sessions_count(self):
        """获取活跃会话数量（用于监控）"""
        return len(self.session_histories)