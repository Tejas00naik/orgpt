from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    session_data_url = models.URLField(max_length=300, blank=True, null=True)  # Storing the URL to the S3 object

    def __str__(self):
        return f"Session {self.id} for {self.user.username}"
