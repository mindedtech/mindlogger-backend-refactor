import hashlib
import uuid
from apps.applets.crud.applets import AppletsCRUD
from apps.authentication.services.security import AuthenticationService
from apps.integrations.prolific.domain import ProlificAnswerParams
from apps.shared.hashing import hash_sha224
from apps.subjects.domain import SubjectCreate
from apps.subjects.services.subjects import SubjectsService
from apps.users.cruds.user import UsersCRUD
from apps.users.db.schemas import UserSchema
from config import settings

class ProlificUserService:
    def __init__(self, session, prolific_participant: ProlificAnswerParams) -> None:
        self.session = session
        self.prolific_pid = prolific_participant.prolific_pid
        self.prolific_session_id = prolific_participant.session_id
        self.prolific_study_id = prolific_participant.study_id
        

    async def get_or_create_prolific_respondent(self) -> UserSchema:
        hash_object = hashlib.sha256(f"{self.prolific_pid}-{self.prolific_session_id}".encode('utf-8'))
        prolific_respondent_id = uuid.UUID(hash_object.hexdigest()[:32])

        crud = UsersCRUD(self.session)

        prolific_respondent = await crud.get_prolific_respondent(prolific_respondent_id)
        if not prolific_respondent:
            email = f"{self.prolific_pid}-{self.prolific_session_id}{settings.prolific_respondent.email}"
            prolific_respondent = UserSchema(
                id=prolific_respondent_id,
                email=hash_sha224(email),
                first_name=settings.prolific_respondent.first_name,
                last_name=settings.prolific_respondent.last_name,
                hashed_password=AuthenticationService(self.session).get_password_hash(
                    settings.anonymous_respondent.password
                ),
                email_encrypted=email,
                is_prolific_respondent=True,
            )

            return await crud.save(prolific_respondent)
        
        return prolific_respondent
    
    async def create_subject_for_prolific_respondent(self, prolific_respondent: UserSchema, applet_id: uuid.UUID) -> None:
        subject_service = SubjectsService(self.session, prolific_respondent.id)
        subject = await subject_service.get_by_user_and_applet(prolific_respondent.id, applet_id)
        applet = await AppletsCRUD(session=self.session).get_by_id(applet_id)

        if not subject or subject.is_deleted:
            await subject_service.create(
                SubjectCreate(
                    applet_id=applet_id,
                    creator_id=applet.creator_id,
                    user_id=prolific_respondent.id,
                    first_name=prolific_respondent.first_name,
                    last_name=prolific_respondent.last_name,
                    secret_user_id=settings.anonymous_respondent.secret_user_id,
                    email=settings.anonymous_respondent.email,
                    nickname=f"ProlificPID={self.prolific_pid}/SessionID={self.prolific_session_id}/StudyID={self.prolific_study_id}"
                )
            )
        # else: Do nothing, subject already exists