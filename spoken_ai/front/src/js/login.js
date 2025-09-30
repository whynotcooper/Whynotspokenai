class LoginManager {
    constructor() {
        this.initEventListeners();
        this.isLoading = false;
    }

    initEventListeners() {
        // 表单提交
        const loginForm = document.getElementById('loginForm');
        loginForm.addEventListener('submit', (e) => this.handleLogin(e));

        // 微信登录
        const wechatLogin = document.getElementById('wechatLogin');
        wechatLogin.addEventListener('click', () => this.showWechatQRCode());

        // 微信小程序登录
        const wechatMiniProgram = document.getElementById('wechatMiniProgram');
        wechatMiniProgram.addEventListener('click', () => this.handleWechatMiniProgram());

        // 关闭弹窗
        const closeModal = document.getElementById('closeModal');
        closeModal.addEventListener('click', () => this.hideWechatQRCode());

        // 注册链接
        const registerLink = document.getElementById('registerLink');
        registerLink.addEventListener('click', (e) => {
            e.preventDefault();
            this.showRegisterForm();
        });

        // 点击弹窗外部关闭
        const modal = document.getElementById('wechatModal');
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.hideWechatQRCode();
            }
        });
    }

    async handleLogin(e) {
        e.preventDefault();
        
        if (this.isLoading) return;
        
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const rememberMe = document.getElementById('remember').checked;

        if (!this.validateEmail(email)) {
            this.showMessage('请输入有效的邮箱地址', 'error');
            return;
        }

        if (password.length < 6) {
            this.showMessage('密码长度至少6位', 'error');
            return;
        }

        this.setLoading(true);

        try {
            // 模拟API调用
            await this.mockLoginAPI({ email, password, rememberMe });
            
            this.showMessage('登录成功！', 'success');
            
            // 跳转到主页面
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1000);

        } catch (error) {
            this.showMessage(error.message, 'error');
        } finally {
            this.setLoading(false);
        }
    }

    async mockLoginAPI(credentials) {
        // 模拟网络延迟
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        // 模拟登录验证
        if (credentials.email === 'demo@example.com' && credentials.password === '123456') {
            return { success: true, token: 'mock_jwt_token', user: { name: 'Demo User' } };
        } else {
            throw new Error('邮箱或密码错误');
        }
    }

    showWechatQRCode() {
        const modal = document.getElementById('wechatModal');
        const qrcode = document.getElementById('wechatQrcode');
        
        // 显示弹窗
        modal.style.display = 'flex';
        
        // 模拟生成二维码
        setTimeout(() => {
            qrcode.innerHTML = `
                <div class="qrcode-success">
                    <i class="fab fa-weixin" style="color: #07c160; font-size: 3rem; margin-bottom: 10px;"></i>
                    <p style="color: #666; font-size: 0.9rem;">请使用微信扫描二维码</p>
                    <div style="margin-top: 10px; padding: 10px; background: #f0f9ff; border-radius: 8px;">
                        <p style="color: #07c160; font-size: 0.8rem; margin: 0;">模拟二维码 - 扫描后自动登录</p>
                    </div>
                </div>
            `;
            
            // 模拟扫码成功
            setTimeout(() => {
                this.handleWechatLoginSuccess();
            }, 3000);
        }, 1000);
    }

    hideWechatQRCode() {
        const modal = document.getElementById('wechatModal');
        modal.style.display = 'none';
    }

    handleWechatLoginSuccess() {
        this.hideWechatQRCode();
        this.showMessage('微信登录成功！', 'success');
        
        setTimeout(() => {
            window.location.href = '/dashboard';
        }, 1000);
    }

    handleWechatMiniProgram() {
        this.showMessage('正在打开微信小程序...', 'info');
        
        // 在实际应用中，这里会调用微信小程序的登录API
        setTimeout(() => {
            this.showMessage('小程序登录成功！', 'success');
            window.location.href = '/dashboard';
        }, 2000);
    }

    showRegisterForm() {
        this.showMessage('注册功能即将开放，敬请期待！', 'info');
    }

    validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    setLoading(loading) {
        this.isLoading = loading;
        const loginBtn = document.getElementById('loginBtn');
        const btnText = loginBtn.querySelector('.btn-text');
        const btnLoader = loginBtn.querySelector('.btn-loader');

        if (loading) {
            btnText.style.opacity = '0';
            btnLoader.style.display = 'block';
            loginBtn.disabled = true;
        } else {
            btnText.style.opacity = '1';
            btnLoader.style.display = 'none';
            loginBtn.disabled = false;
        }
    }

    showMessage(message, type = 'info') {
        // 移除现有的消息
        const existingMessage = document.querySelector('.message-toast');
        if (existingMessage) {
            existingMessage.remove();
        }

        // 创建新消息
        const toast = document.createElement('div');
        toast.className = `message-toast message-${type}`;
        toast.textContent = message;
        
        // 添加样式
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 1001;
            animation: slideIn 0.3s ease;
            max-width: 300px;
        `;

        // 根据类型设置背景色
        const colors = {
            success: '#07c160',
            error: '#ff4757',
            info: '#2f3542',
            warning: '#ffa502'
        };
        toast.style.background = colors[type] || colors.info;

        document.body.appendChild(toast);

        // 3秒后自动消失
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// 添加消息动画样式
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// 初始化登录管理器
document.addEventListener('DOMContentLoaded', () => {
    new LoginManager();
});