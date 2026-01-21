from fastapi import FastAPI
import uvicorn
from pdd_app.api import (model_pdd, user, auth,
                         exams, question, category, admin)

pdd_app = FastAPI()
pdd_app.include_router(model_pdd.pdd_router)
pdd_app.include_router(user.user_router)
pdd_app.include_router(admin.admin_router)
pdd_app.include_router(auth.auth_router)
pdd_app.include_router(exams.exam_router)
pdd_app.include_router(question.question_router)
pdd_app.include_router(category.category_router)





if __name__ == '__main__':
    uvicorn.run(pdd_app, host='127.0.0.1', port=8011)