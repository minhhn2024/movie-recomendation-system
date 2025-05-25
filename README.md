# Movie recommendation system project

<a href="https://github.com/fastapi/full-stack-fastapi-template/actions?query=workflow%3ATest" target="_blank"><img src="https://github.com/fastapi/full-stack-fastapi-template/workflows/Test/badge.svg" alt="Test"></a>
<a href="https://coverage-badge.samuelcolvin.workers.dev/redirect/fastapi/full-stack-fastapi-template" target="_blank"><img src="https://coverage-badge.samuelcolvin.workers.dev/fastapi/full-stack-fastapi-template.svg" alt="Coverage"></a>

follow my steps.

**Step1:** download this pre-train file, extract 3 folders and paste them to `movie-recomendation-system\backend\app`
https://drive.google.com/file/d/1EA_-KxgpwDybeFwbBEK6eukqKPk0xwjr/view?usp=sharing
result should like this 
![image](https://github.com/user-attachments/assets/8aaa640b-1912-4d18-a864-cb09c3dd5889)

**Step2:** install `Docker desktop`, and `window subsystem for linux` command line 
- install `Docker desktop`
- install `Window subsystem for linux`: https://learn.microsoft.com/en-us/windows/wsl/install
- now connect wsl to docker by `WSL integration`
![image](https://github.com/user-attachments/assets/e3f599cf-60f1-49df-b631-4dda4196895a)
- save and restart docker
  
**Step3:** now in window CMD, switch to bash shell command promp `wsl -d <your_distro_name>` or `wsl -l` to show all distributions
- change directory to the folder of project such as `/mnt/c/Users/Projects/movie-recomendation-system`
- run command `docker-compose up -d` and wait for the build process completed.

now in docker desktop we have a compose task 
![image](https://github.com/user-attachments/assets/8888224e-164f-4905-8bf8-7e76edaf7af7)
go to visit `http://localhost:5173/` 
