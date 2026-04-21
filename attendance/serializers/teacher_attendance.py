from rest_framework import serializers
from attendance.models import TeacherAttendance
from teachers.serializers.teacher import TeacherMinimalSerializer
from users.serializers.user.minimal import UserMinimalSerializer


class TeacherAttendanceMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for teacher attendance."""

    teacher = TeacherMinimalSerializer(read_only=True)

    class Meta:
        model = TeacherAttendance
        fields = ["id", "teacher", "date", "status", "time_in"]
        read_only_fields = fields


class TeacherAttendanceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a teacher attendance record."""

    teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=Teacher.objects.all(), source="teacher"
    )
    recorded_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="recorded_by", required=False, allow_null=True
    )

    class Meta:
        model = TeacherAttendance
        fields = "__all__"

    def create(self, validated_data) -> TeacherAttendance:
        from attendance.services.teacher_attendance import TeacherAttendanceService

        return TeacherAttendanceService.create_attendance(**validated_data)


class TeacherAttendanceUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a teacher attendance record."""

    class Meta:
        model = TeacherAttendance
        fields = ["status", "time_in", "time_out", "late_minutes", "remarks"]

    def update(self, instance, validated_data) -> TeacherAttendance:
        from attendance.services.teacher_attendance import TeacherAttendanceService

        return TeacherAttendanceService.update_attendance(instance, validated_data)


class TeacherAttendanceDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a teacher attendance record."""

    teacher = TeacherMinimalSerializer(read_only=True)
    recorded_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = TeacherAttendance
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]